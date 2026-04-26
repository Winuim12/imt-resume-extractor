from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from time import perf_counter

import fitz
import pytesseract
from pypdf import PdfReader
from PIL import Image

from src.config import settings


@dataclass
class ExtractionResult:
    text: str
    method: str
    page_count: int
    elapsed_seconds: float


def _extract_text_pdf(pdf_path: Path) -> tuple[str, int]:
    reader = PdfReader(str(pdf_path))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip(), len(reader.pages)


def _extract_text_ocr(pdf_path: Path) -> tuple[str, int]:
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        image_bytes = pix.tobytes("png")
        image = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        text_parts.append(text or "")
    return "\n".join(text_parts).strip(), len(doc)


def extract_resume_text(pdf_path: Path) -> ExtractionResult:
    start = perf_counter()
    text, page_count = _extract_text_pdf(pdf_path)

    if len(text) > 200:
        elapsed = perf_counter() - start
        return ExtractionResult(
            text=text,
            method="text-layer",
            page_count=page_count,
            elapsed_seconds=round(elapsed, 2),
        )

    ocr_text, ocr_pages = _extract_text_ocr(pdf_path)
    elapsed = perf_counter() - start
    return ExtractionResult(
        text=ocr_text,
        method="ocr",
        page_count=ocr_pages,
        elapsed_seconds=round(elapsed, 2),
    )
