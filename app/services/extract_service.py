from pdf2image import convert_from_path
import pdfplumber
import pymupdf4llm

def is_scanned(page_text):
    return len(page_text.strip()) < 10

def extract_text_from_pdf(pdf_path):
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text()
            if is_scanned(txt):
                img = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)[0]
                img.save(f"page_{i+1}.png")
            else:
                all_text += txt + "\n" + "-"*60 + "\n\n"
    return all_text

class PDFExtractor:
    def extract_to_markdown(self, pdf_path: str) -> str:
        """Extract PDF content and convert to markdown"""
        try:
            # Use existing extraction logic
            md_text = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
            
            # Force garbage collection to ensure file handles are closed
            import gc
            gc.collect()
            
            # Ensure we return a string - pymupdf4llm with page_chunks=True returns a list
            if isinstance(md_text, list):
                # Each item in the list is a dict with 'text' and 'metadata'
                text_parts = []
                for item in md_text:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    else:
                        text_parts.append(str(item))
                md_text = '\n\n'.join(text_parts)
            elif not isinstance(md_text, str):
                md_text = str(md_text)
            
            return md_text
        except Exception as e:
            # Force garbage collection even on error
            import gc
            gc.collect()
            raise Exception(f"PDF extraction failed: {str(e)}")