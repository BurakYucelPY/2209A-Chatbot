# data/pdfs içindeki TÜM PDF'leri okuyup metni data/text'e .txt olarak kaydeder.
import os, sys
import fitz  # PyMuPDF

ROOT = os.path.dirname(__file__)
PDF_DIR = os.path.join(ROOT, "data", "pdfs")
OUT_DIR = os.path.join(ROOT, "data", "text")
os.makedirs(OUT_DIR, exist_ok=True)

def pdf_to_txt(pdf_path, out_path):
    with fitz.open(pdf_path) as doc:
        with open(out_path, "w", encoding="utf-8") as f:
            for i, page in enumerate(doc):
                text = page.get_text("text") or ""
                f.write(f"\n\n=== [SAYFA {i+1}] ===\n{text}")

def main():
    if not os.path.isdir(PDF_DIR):
        print("Klasör bulunamadı:", PDF_DIR); sys.exit(1)
    pdfs = [p for p in os.listdir(PDF_DIR) if p.lower().endswith(".pdf")]
    if not pdfs:
        print("data/pdfs içinde PDF yok."); sys.exit(1)
    print(f"{len(pdfs)} PDF bulundu. Çıktı klasörü: {OUT_DIR}")
    for name in pdfs:
        in_path = os.path.join(PDF_DIR, name)
        out_path = os.path.join(OUT_DIR, os.path.splitext(name)[0] + ".txt")
        pdf_to_txt(in_path, out_path)
        print("✓", name, "->", os.path.relpath(out_path, ROOT))

if __name__ == "__main__":
    main()
