import pdfplumber
from pdf2image import convert_from_path
from PIL import Image

def is_scanned(page_text):
    return len(page_text.strip()) < 10  # crude filter

# Add more PDF-related utilities as needed
