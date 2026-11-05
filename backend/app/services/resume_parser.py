import io
import re
import os
import fitz  # PyMuPDF
import docx
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class ResumeParserService:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, bool]:
        """
        Extract text from a PDF file using PyMuPDF.
        If extracted text is under 40 characters (likely scanned/image PDF),
        attempts OCR fallback using pytesseract.
        Returns: (extracted_text, ocr_applied)
        """
        extracted_text = ""
        ocr_applied = False
        
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text = page.get_text()
                if text:
                    extracted_text += text + "\n"
            
            # Check if text is suspiciously short (scanned PDF)
            if len(extracted_text.strip()) < 40 and PYTESSERACT_AVAILABLE:
                try:
                    ocr_text = ""
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_text += pytesseract.image_to_string(img) + "\n"
                    if len(ocr_text.strip()) > len(extracted_text.strip()):
                        extracted_text = ocr_text
                        ocr_applied = True
                except Exception as ocr_err:
                    # OCR fallback optional/soft failure
                    pass
            doc.close()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF file: {str(e)}")

        return ResumeParserService.clean_text(extracted_text), ocr_applied

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """
        Extract text from a DOCX file using python-docx.
        """
        try:
            file_stream = io.BytesIO(file_bytes)
            doc = docx.Document(file_stream)
            full_text = []
            for para in doc.paragraphs:
                if para.text:
                    full_text.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))
            text = "\n".join(full_text)
            return ResumeParserService.clean_text(text)
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX file: {str(e)}")

    @staticmethod
    def parse_resume(file_bytes: bytes, file_name: str) -> tuple[str, bool, str]:
        """
        Dispatches to PDF or DOCX extractor based on extension.
        Returns: (extracted_text, ocr_applied, file_type)
        """
        lower_name = file_name.lower()
        if lower_name.endswith(".pdf"):
            text, ocr = ResumeParserService.extract_text_from_pdf(file_bytes)
            return text, ocr, "pdf"
        elif lower_name.endswith(".docx") or lower_name.endswith(".doc"):
            text = ResumeParserService.extract_text_from_docx(file_bytes)
            return text, False, "docx"
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX files.")

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Remove null bytes and excessive whitespace
        text = text.replace("\x00", " ")
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join([line for line in lines if line])
        return cleaned

