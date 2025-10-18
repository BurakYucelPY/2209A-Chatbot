# sor_chroma.py
# chroma_store'dan en ilgili parçaları bulur, Gemini 2.0 Flash ile cevap üretir.

import os, sys
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from google import genai

ROOT = os.path.dirname(__file__)
CHROMA_DIR = os.path.join(ROOT, "chroma_store")
COLLECTION = "dokumanlar"

# Aynı embedding ile yükleyelim (bge-m3)
EMB = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True}
)

def get_retriever(k=4):
    vs = Chroma(
        collection_name=COLLECTION,
        embedding_function=EMB,
        persist_directory=CHROMA_DIR
    )
    # LangChain retriever yerine direkt similarity_search kullanacağız
    return vs

def answer(question: str, top_k: int = 4):
    # 1) En alakalı parçaları getir
    vs = get_retriever(k=top_k)
    docs = vs.similarity_search(question, k=top_k)
    context = "\n\n".join([d.page_content for d in docs])

    # 2) Gemini ile yanıtla
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "GEMINI_API_KEY yok (.env'yi kontrol et).", []

    client = genai.Client(api_key=api_key)

    prompt = (
        "Aşağıdaki BAĞLAMA dayanarak kısa ve net Türkçe bir cevap yaz. "
        "Bağlamda yoksa 'Kaynaklarda net bilgi bulamadım' de. "
        "Cevabın sonunda 1-2 madde halinde kısa öneri ver.\n\n"
        f"BAĞLAM:\n{context}\n\nSORU: {question}\n\nCEVAP:"
    )

    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return (resp.text or "").strip(), docs

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
