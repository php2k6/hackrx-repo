from pdf2image import convert_from_path
import fitz  # PyMuPDF
import camelot


def pdf_to_structured_data_pymupdf(pdf_path):
    """Extract structured text & tables with style info using PyMuPDF + Camelot."""
    doc = fitz.open(pdf_path)
    pages_data = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        elements = []

        for b in blocks:
            if "lines" in b:
                for line in b["lines"]:
                    # Keep numbers + heading text exactly as in PDF
                    line_text = "".join(
                        (span["text"] +" ") if not span["text"].endswith(" ") else span["text"]
                        for span in line["spans"]
                    ).strip()
                    if not line_text:
                        continue
                    avg_font_size = sum(
                        span["size"] for span in line["spans"]) / len(line["spans"])
                    is_bold = any("Bold" in (span["font"] or "")for span in line["spans"])
                    elements.append({
                        "text": line_text,
                        "font_size": avg_font_size,
                        "is_bold": is_bold,
                        "type": "text"
                    })

        # Extract tables for this page
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_num))
            for t_i, table in enumerate(tables, start=1):
                elements.append({
                    "text": table.df.to_dict(orient="records"),
                    "font_size": 0,
                    "is_bold": False,
                    "type": "table"
                })
        except Exception:
            pass

        pages_data.append({"page": page_num, "elements": elements})

    return pages_data


class PDFExtractor:
    def extract_structured_data(self, pdf_path: str) -> list:
        """Extract structured data with font info using PyMuPDF + Camelot"""
        try:
            return pdf_to_structured_data_pymupdf(pdf_path)
        except Exception as e:
            raise Exception(f"Structured data extraction failed: {str(e)}")
