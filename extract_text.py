
from pdf2image import convert_from_path
import pdfplumber


def is_scanned(page_text):
    return len(page_text.strip()) < 10  # crude filter

def extract_text_from_pdf(pdf_path):
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text()
            if is_scanned(txt):
                print("Scanned page detected")
                img = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)[0]
                img.save(f"page_{i+1}.png")  # run OCR only here
            else:
                all_text += txt + "\n" + "-"*60 + "\n\n"
    return all_text
