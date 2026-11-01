import os
from typing import Dict, Any, List
from io import BytesIO

from pdfminer.high_level import extract_text
from pypdf import PdfReader
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from langdetect import detect

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from io import StringIO

from src.utils.text import normalize_ar_digits, strip_tatweel, clean_spaces
from src.utils.text import strip_long_underscores
class OCRService:

    @staticmethod
    async def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF. If text layer missing (scanned PDF),
        fallback to OCR service (future extension: Azure / Doctr).
        Returns: { text: str, pages: int, language: str, page_offsets: List[int] }
        page_offsets[i] = starting character offset of page i within the normalized full text.
        """
        try:
            # Count pages with pypdf
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                pages = len(reader.pages)

            # Per-page extraction with pdfminer to compute page_offsets
            page_texts = []
            for i in range(pages):
                buf = StringIO()
                with open(file_path, "rb") as f2:
                    extract_text_to_fp(f2, buf, laparams=LAParams(), page_numbers=[i])
                page_texts.append(buf.getvalue() or "")

            # Normalize each page then join to single text
            norm_pages = [OCRService._preprocess_text(t) for t in page_texts]
            text = "".join(norm_pages) or ""

            # Fallback to whole-file text if result is too small (handles odd PDFs)
            if len(text.strip()) < 50:
                text = extract_text(file_path) or ""
                if len(text.strip()) < 50:
                    text = await OCRService._fallback_ocr_pdf(file_path)
                text = OCRService._preprocess_text(text)
                # If we didn’t build page-wise text, just return no offsets
                page_offsets = []
            else:
                # Build page_offsets over normalized pages
                page_offsets = []
                acc = 0
                for pt in norm_pages:
                    page_offsets.append(acc)
                    acc += len(pt)

            language = OCRService._detect_language(text)

            return {
                "text": text,
                "pages": pages,
                "language": language,
                "page_offsets": page_offsets,  # may be [] if unknown
            }

        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")

    @staticmethod
    async def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
        """
        Extract from a DOCX, body paragraphs and tables in document order.
        Pages follow the page breaks Word stored when the file was last saved
        (w:lastRenderedPageBreak and explicit page breaks), so citations can name a page.
        Returns: { text: str, pages: int, language: str, page_offsets: List[int] }
        """
        try:
            doc = Document(file_path)
            body = doc.element.body

            # Collect raw text per page
            page_texts: List[List[str]] = [[]]
            for block in body.iterchildren():
                tag = block.tag.rsplit("}", 1)[-1]
                if tag == "p":
                    block_text = Paragraph(block, doc).text
                elif tag == "tbl":
                    cells = []
                    for row in Table(block, doc).rows:
                        for cell in row.cells:
                            ct = cell.text.strip()
                            if ct and (not cells or cells[-1] != ct):
                                cells.append(ct)
                    block_text = " ".join(cells)
                else:
                    continue

                breaks = len(block.xpath(".//w:lastRenderedPageBreak | .//w:br[@w:type='page']"))
                # A break inside this block starts a new page at the block (close enough for citations)
                for _ in range(breaks):
                    if page_texts[-1]:
                        page_texts.append([])
                if block_text and block_text.strip():
                    page_texts[-1].append(block_text)

            norm_pages = [OCRService._preprocess_text(" ".join(p)) for p in page_texts]
            norm_pages = [p for p in norm_pages if p]
            text = " ".join(norm_pages)

            page_offsets = []
            acc = 0
            for pt in norm_pages:
                page_offsets.append(acc)
                acc += len(pt) + 1

            language = OCRService._detect_language(text)

            return {
                "text": text,
                "pages": max(1, len(norm_pages)),
                "language": language,
                "page_offsets": page_offsets if len(norm_pages) > 1 else [],
            }

        except Exception as e:
            raise Exception(f"DOCX extraction error: {str(e)}")

    # ---------------- INTERNAL HELPERS ---------------- #

    @staticmethod
    async def _fallback_ocr_pdf(file_path: str) -> str:
        """
        Future OCR fallback logic (Azure Document Intelligence or Doctr).
        Currently returns empty string until OCR added.
        """
        # TODO: implement OCR fallback → integrate with ocr_service.py using Doctr or Azure
        return ""

    @staticmethod
    def _preprocess_text(text: str) -> str:
        """
        Cleanup for LLM/RAG: remove extra whitespace, normalize Arabic digits, strip tatweel
        """
        try:
            text = normalize_ar_digits(text)
            text = strip_tatweel(text)
            text = clean_spaces(text)
            text = strip_long_underscores(text)
        except Exception:
            pass
        return text

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        Basic lang detection (English/Arabic). Extend if needed.
        """
        try:
            lang = detect(text)
            return "ar" if lang.startswith("ar") else "en"
        except Exception:
            return "en"