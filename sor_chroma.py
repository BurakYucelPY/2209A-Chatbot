# sor_chroma.py
# Genel amaçlı: Chroma + BGE-m3 + Gemini 2.0 Flash
# - Son 3 mesaj hafızalı (chat_memory.json)
# - Multi-Query (soru genişletme)
# - Dinamik anahtar kelime çıkarımı (kullanıcı sorusuna göre)
# - Odaklı bağlam: sadece ilgili cümleler
# - Sampling ayarları: temperature=0.7, top_p=0.95, top_k=40

import os, sys, json, re, hashlib
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from google import genai
from google.genai import types  # <-- SAMPLING CONFIG İÇİN EKLENDİ

ROOT = os.path.dirname(__file__)
CHROMA_DIR = os.path.join(ROOT, "chroma_store")
COLLECTION = "dokumanlar"

# --- Hafıza ---
MEM_FILE = os.path.join(ROOT, "chat_memory.json")
MAX_TURNS = 3

# --- Embedding ---
EMB = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True}
)

def get_vs():
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=EMB,
        persist_directory=CHROMA_DIR
    )

# ----------------- Hafıza yardımcıları -----------------
def load_history():
    if os.path.exists(MEM_FILE):
        try:
            return json.load(open(MEM_FILE, "r", encoding="utf-8"))
        except Exception:
            return []
    return []

def save_turn(q, a):
    hist = load_history()
    hist.append({"user": q, "assistant": a})
    json.dump(hist[-MAX_TURNS:], open(MEM_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

# ----------------- Metin yardımcıları -----------------
STOPWORDS_TR = {
    "ve","veya","ile","için","ama","fakat","de","da","mi","mı","mu","mü",
    "bir","şu","bu","o","çok","az","olan","olup","olanlar","gibi","vb",
    "nedir","ne","nasıl","hangi","hakkında","üzerine","etmek","yapmak",
    "ben","biz","siz","onlar","var","yok","mı","mi","mu","mü","ki","de","da"
}

def tokenize(text: str):
    toks = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9\-]+", text.lower())
    return [t for t in toks if t not in STOPWORDS_TR and len(t) > 2]

def extract_query_keywords(question: str, topk: int = 8):
    toks = tokenize(question)
    freq = {}
    for t in toks:
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))
    return [w for w,_ in ranked[:topk]] or toks[:topk]

def sentence_split(text: str):
    parts = re.split(r'(?<=[\.\?\!])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def pick_keyword_sentences(text: str, keywords, limit=6):
    sents = sentence_split(text)
    scored = []
    for s in sents:
        score = sum(1 for kw in keywords if kw in s.lower())
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    return [s for _, s in scored[:limit]]

def hash_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

# ----------------- Multi-Query (soruyu çeşitlendir) -----------------
def generate_query_rewrites(client: genai.Client, question: str, n: int = 3):
    prompt = (
        "Aşağıdaki soruyu Türkçe'de 3 kısa, farklı sorguya dönüştür. "
        "Her satıra sadece 1 sorgu yaz, başka metin yazma.\n\n"
        f"Soru: {question}\n\nSorgular:\n"
    )
    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = (resp.text or "").strip()
        rewrites = [line.strip("•-* 1234567890. \t") for line in text.splitlines() if line.strip()]
        return rewrites[:n] if rewrites else [question]
    except Exception:
        return [question]

def retrieve_docs_multiquery(vs: Chroma, question: str, client: genai.Client,
                             per_query_k: int = 4, top_final: int = 10):
    rewrites = generate_query_rewrites(client, question, n=3)
    merged, seen = [], set()
    for q in [question] + rewrites:
        try:
            docs = vs.similarity_search(q, k=per_query_k)
        except Exception:
            docs = []
        for d in docs:
            key = hash_text(d.page_content[:800])
            if key in seen:
                continue
            seen.add(key)
            merged.append(d)
            if len(merged) >= top_final:
                break
        if len(merged) >= top_final:
            break
    return merged

def build_focused_context(docs, question: str):
    """
    Her doküman parçasından, sorudan türetilen dinamik anahtar kelimelere göre
    en alakalı cümleleri seçip kısa bir bağlam oluşturur.
    """
    kws = [kw.lower() for kw in extract_query_keywords(question)]
    blocks = []
    for d in docs:
        src = d.metadata.get("source") or "(kaynak yok)"
        key_sents = pick_keyword_sentences(d.page_content.lower(), kws, limit=4)
        snippet = "\n".join(key_sents) if key_sents else d.page_content[:500]
        snippet = snippet.replace("=== [sayfa", "=== [SAYFA").replace("=== [page", "=== [PAGE")
        blocks.append(f"[KAYNAK: {src}]\n{snippet}")
    ctx = "\n\n---\n\n".join(blocks)
    return ctx[:8000]

def build_prompt(history, context, question):
    # Son 3 turu string'e çevir
    turns = []
    for turn in history[-MAX_TURNS:]:
        turns.append(f"USER: {turn['user']}\nASSISTANT: {turn['assistant']}")
    history_str = "\n\n".join(turns) if turns else "(no prior turns)"

    prompt = (
        "Aşağıda SON 3 TUR konuşma geçmişi, ardından RAG BAĞLAMI ve yeni SORU var.\n"
        "Görevin: BAĞLAM ve KONUŞMA GEÇMİŞİNE dayanarak, kısa ve net TÜRKÇE bir cevap üretmek.\n"
        "\n"
        "KURALLAR:\n"
        "1) Öncelik: Yalnızca bağlamda açıkça yer alan bilgileri kullan.\n"
        "2) Bağlamda doğrudan olmayan ama MAKUL bir çıkarım gerekiyorsa, bunu ayrı bir satırda\n"
        "   'Varsayımlı çıkarım:' etiketiyle belirt ve dayandığın cümleyi/ifadeyi kısaca alıntıla.\n"
        "3) Dış bilgi/ezber kullanma; sayı/tarih uydurma. Belirsizse net söyle.\n"
        "4) İstenen format/proje bölümü (örn. Özet, Amaç, Yöntem, SKA eşleştirme) varsa ona uygun yaz.\n"
        "5) Cevabın sonunda 1-2 maddelik 'Gerekçe' yaz: bağlamdan aldığın ipuçlarını kısaca özetle.\n"
        "6) Ardından 'Kaynaklar:' satırı koy ve BAĞLAM içindeki [KAYNAK: ...] işaretlerinden\n"
        "   en alakalı 1-2 benzersiz dosya adını parantezsiz sırala (fazla uzatma).\n"
        "7) Bağlamda yoksa: 'Kaynaklarda net bilgi bulamadım.' de ve dur.\n"
        "\n"
        "NOTLAR:\n"
        "- Proje metni istenirse sırayla problem → amaç → yöntem (veri/kısa yöntem) → beklenen sonuç → yaygın etki → ilgili SKA numaraları şablonunu kullan.\n"
        "- Liste istenirse kısa ve numarasız madde işaretleri kullan.\n"
        "- Gereksiz tekrar yapma; 6-10 cümleyi geçme (kısa görevlerde daha da kısa tut).\n"
        "\n"
        f"=== GEÇMİŞ ===\n{history_str}\n\n"
        f"=== BAĞLAM ===\n{context}\n\n"
        f"=== SORU ===\n{question}\n\n"
        "=== CEVAP ==="
    )
    return prompt

# ----------------- Ana akış -----------------
def answer(question: str, top_k: int = 10):
    # API
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "GEMINI_API_KEY yok (.env)", []
    client = genai.Client(api_key=api_key)

    # 1) Alakalı parçaları getir (multi-query)
    vs = get_vs()
    docs = retrieve_docs_multiquery(vs, question, client, per_query_k=4, top_final=top_k)

    # 2) Bağlamı odaklı kur
    context = build_focused_context(docs, question)

    # 3) Son 3 tur hafızalı cevap
    history = load_history()
    prompt = build_prompt(history, context, question)

    # === ÇEŞİTLİLİK AYARLARI (senin istediğin) ===
    cfg = types.GenerateContentConfig(
        temperature=0.7,  # biraz çeşitlilik
        top_p=0.95,
        top_k=40,
        candidate_count=1
    )

    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=cfg
    )
    answer_text = (resp.text or "").strip()

    # 4) Hafızaya yaz
    save_turn(question, answer_text)
    return answer_text, docs

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Kullanım: py sor_chroma.py "sorunuz"')
        sys.exit(0)
    q = " ".join(sys.argv[1:])
    ans, refs = answer(q)
    print("\n=== CEVAP ===\n" + ans)
    print("\n=== KAYNAKLAR ===")
    for d in refs:
        print("-", d.metadata.get("source", "(yok)"))
