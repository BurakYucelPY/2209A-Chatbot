# indeks_olustur_chroma.py
# data/text içindeki .txt dosyalarını chunk'lar, BAAI/bge-m3 ile embed eder,
# ChromaDB'ye (chroma_store/) kalıcı olarak yazar.

import os, sys, glob
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

ROOT = os.path.dirname(__file__)
TEXT_DIR = os.path.join(ROOT, "data", "text")
CHROMA_DIR = os.path.join(ROOT, "chroma_store")
COLLECTION = "dokumanlar"

# --- Ayarlar ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
EMB_MODEL = "BAAI/bge-m3"  # seçiminiz
EMB = HuggingFaceEmbeddings(
    model_name=EMB_MODEL,
    # BGE ailesi için önerilir: kosinüs benzerlikte normalize
    encode_kwargs={"normalize_embeddings": True}
)

def read_all_texts():
    files = sorted(glob.glob(os.path.join(TEXT_DIR, "*.txt")))
    if not files:
        print("data/text içinde .txt yok. Önce pdfden_metin_cikar.py çalıştır.")
        sys.exit(1)
    texts, metas = [], []
    for fp in files:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read().strip()
        # Boşsa atla
        if not txt:
            continue
        texts.append(txt)
        metas.append({"source": os.path.relpath(fp, ROOT)})
    return texts, metas

def build_index(rebuild: bool = False):
    if rebuild and os.path.isdir(CHROMA_DIR):
        # koleksiyonu sıfırla
        for fn in os.listdir(CHROMA_DIR):
            p = os.path.join(CHROMA_DIR, fn)
            if os.path.isdir(p):
                # klasörü temizlemek için basitçe silip yeniden oluşturmak yerine
                # yeni bir persist_directory ile de gidebilirdiniz
                pass
        # Kolay yol: eski dizini komple kaldır
        import shutil
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)

    # Var olanı yüklemeyi dene
    if (not rebuild) and os.path.isdir(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        vs = Chroma(
            collection_name=COLLECTION,
            embedding_function=EMB,
            persist_directory=CHROMA_DIR,
        )
        print("Mevcut Chroma indeksi yüklendi.")
        return vs

    # Yoksa oluştur
    texts, metas = read_all_texts()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    docs = splitter.create_documents(texts, metadatas=metas)
    print(f"Toplam {len(docs)} parça (chunk) oluşturuldu.")

    vs = Chroma.from_documents(
        documents=docs,
        embedding=EMB,
        collection_name=COLLECTION,
        persist_directory=CHROMA_DIR,
    )
    vs.persist()
    print(f"Chroma indeksi yazıldı: {CHROMA_DIR}")
    return vs

if __name__ == "__main__":
    rebuild = ("--rebuild" in sys.argv)
    build_index(rebuild=rebuild)
