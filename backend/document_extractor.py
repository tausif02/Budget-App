# document_extractor.py
from io import BytesIO
from pathlib import Path

import pymupdf
import pytesseract
from PIL import (
    Image,
    ImageFilter,
    ImageOps,
)


RECEIPT_OCR_CONFIG = (
    "--oem 3 "
    "--psm 6 "
    "-c preserve_interword_spaces=1"
)

DOCUMENT_OCR_CONFIG = (
    "--oem 3 "
    "--psm 3 "
    "-c preserve_interword_spaces=1"
)

MINIMUM_OCR_WIDTH = 1200


def prepare_image(
    image: Image.Image
) -> Image.Image:
    """Improve an image before OCR."""
    prepared_image = ImageOps.exif_transpose(image)
    prepared_image = ImageOps.grayscale(prepared_image)
    prepared_image = ImageOps.autocontrast(
        prepared_image,
        cutoff=1,
    )

    if prepared_image.width < MINIMUM_OCR_WIDTH:
        scale = (
            MINIMUM_OCR_WIDTH
            / prepared_image.width
        )

        resized_width = round(
            prepared_image.width * scale
        )

        resized_height = round(
            prepared_image.height * scale
        )

        prepared_image = prepared_image.resize(
            (resized_width, resized_height),
            Image.Resampling.LANCZOS,
        )

    prepared_image = prepared_image.filter(
        ImageFilter.SHARPEN
    )

    return prepared_image


def run_ocr(
    image: Image.Image,
    config: str,
) -> str:
    """Run Tesseract with the requested layout mode."""
    return pytesseract.image_to_string(
        image,
        lang="eng",
        config=config,
    ).strip()


def extract_image_text(file_bytes: bytes) -> str:
    """Extract text from a JPG or PNG receipt."""
    with Image.open(BytesIO(file_bytes)) as image:
        prepared_image = prepare_image(image)

        return run_ocr(
            image=prepared_image,
            config=RECEIPT_OCR_CONFIG,
        )


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from digital or scanned PDF pages."""
    extracted_pages = []

    with pymupdf.open(
        stream=file_bytes,
        filetype="pdf",
    ) as document:
        for page in document:
            # Digital documents usually contain selectable text.
            page_text = page.get_text("text").strip()

            if page_text:
                extracted_pages.append(page_text)
                continue

            # Scanned PDFs must be rendered as images first.
            page_image = page.get_pixmap(
                dpi=250,
                alpha=False,
            )

            with Image.open(
                BytesIO(page_image.tobytes("png"))
            ) as image:
                prepared_image = prepare_image(image)

                page_text = run_ocr(
                    image=prepared_image,
                    config=DOCUMENT_OCR_CONFIG,
                )

                extracted_pages.append(page_text)

    return "\n\n".join(extracted_pages).strip()


def extract_document_text(
    filename: str,
    file_bytes: bytes,
) -> str:
    """Choose the correct extraction method."""
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_bytes)

    if extension in {
        ".jpg",
        ".jpeg",
        ".png",
    }:
        return extract_image_text(file_bytes)

    raise ValueError(
        "Only PDF, JPG, JPEG, and PNG files are supported"
    )
