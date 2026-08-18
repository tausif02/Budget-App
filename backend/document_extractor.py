from io import BytesIO
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image, ImageOps


def prepare_image(image: Image.Image) -> Image.Image:
    """Improve an image before OCR."""
    image = ImageOps.exif_transpose(image)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)

    return image


def extract_image_text(file_bytes: bytes) -> str:
    """Extract text from a JPG or PNG receipt."""
    with Image.open(BytesIO(file_bytes)) as image:
        prepared_image = prepare_image(image)

        return pytesseract.image_to_string(
            prepared_image,
            lang="eng"
        ).strip()


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from digital or scanned PDF pages."""
    extracted_pages = []

    with pymupdf.open(
        stream=file_bytes,
        filetype="pdf"
    ) as document:
        for page in document:
            # Digital statements often already contain selectable text.
            page_text = page.get_text("text").strip()

            if page_text:
                extracted_pages.append(page_text)
                continue

            # If no embedded text exists, render the page and use OCR.
            page_image = page.get_pixmap(
                dpi=200,
                alpha=False
            )

            with Image.open(
                BytesIO(page_image.tobytes("png"))
            ) as image:
                prepared_image = prepare_image(image)

                page_text = pytesseract.image_to_string(
                    prepared_image,
                    lang="eng"
                ).strip()

                extracted_pages.append(page_text)

    return "\n\n".join(extracted_pages).strip()


def extract_document_text(
    filename: str,
    file_bytes: bytes
) -> str:
    """Choose the correct extraction method."""
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_bytes)

    if extension in {".jpg", ".jpeg", ".png"}:
        return extract_image_text(file_bytes)

    raise ValueError(
        "Only PDF, JPG, JPEG, and PNG files are supported"
    )
