"""Utility functions for generating test PDFs."""

import tempfile
import os
from pathlib import Path
from typing import Optional, List, Tuple
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import Color, black, white, red, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from pypdf import PdfWriter, PdfReader
import io


def create_basic_pdf(
    text: str = "Sample CV Text",
    font_size: int = 12,
    pages: int = 1,
    author: str = "Test Author",
    title: str = "Test CV",
    background_color: Optional[Color] = None,
    text_color: Color = black,
    add_link: Optional[str] = None,
    add_image: bool = False,
    corrupt: bool = False,
) -> bytes:
    """Create a basic PDF with specified characteristics.

    Args:
        text: Text content to include
        font_size: Font size for text
        pages: Number of pages
        author: PDF author metadata
        title: PDF title metadata
        background_color: Background color (None for white)
        text_color: Text color
        add_link: URL to add as a link
        add_image: Whether to add an image
        corrupt: Whether to corrupt the PDF

    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()

    # Create canvas
    c = canvas.Canvas(buffer, pagesize=letter)

    # Set metadata
    c.setAuthor(author)
    c.setTitle(title)

    for page_num in range(pages):
        # Set background color if specified
        if background_color:
            c.setFillColor(background_color)
            c.rect(0, 0, letter[0], letter[1], fill=1)

        # Set text color and font
        c.setFillColor(text_color)
        c.setFont("Helvetica", font_size)

        # Add text
        y_position = letter[1] - 100  # Start near top
        page_text = f"{text} - Page {page_num + 1}" if pages > 1 else text
        c.drawString(100, y_position, page_text)

        # Add link if specified
        if add_link:
            c.linkURL(add_link, (100, y_position - 20, 300, y_position), relative=1)
            c.drawString(100, y_position - 20, f"Link: {add_link}")

        # Add image if specified (create actual image object)
        if add_image:
            from reportlab.lib.utils import ImageReader
            from PIL import Image as PILImage
            import io as image_io

            # Create a small PIL image
            img = PILImage.new("RGB", (50, 50), color="red")
            img_buffer = image_io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            # Add the image to the PDF
            c.drawImage(
                ImageReader(img_buffer), 100, y_position - 100, width=50, height=50
            )

        # Start new page if not the last one
        if page_num < pages - 1:
            c.showPage()

    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Corrupt the PDF if requested
    if corrupt:
        # Truncate the PDF to make it corrupted
        pdf_bytes = pdf_bytes[: len(pdf_bytes) // 2]

    return pdf_bytes


def create_large_pdf(target_size_kb: float = 600) -> bytes:
    """Create a PDF that exceeds the size limit.

    Args:
        target_size_kb: Target size in KB

    Returns:
        PDF content as bytes
    """
    # Create a PDF with lots of text and images to make it large
    large_text = (
        "This is a very long text that will be repeated many times to make the PDF large. "
        * 5000
    )

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setAuthor("Test Author")
    c.setTitle("Large Test PDF")

    # Add many pages with lots of text and images
    for page in range(50):  # Many more pages
        c.setFont("Helvetica", 12)
        y_position = letter[1] - 50

        # Add text in chunks
        text_chunks = [large_text[i : i + 70] for i in range(0, len(large_text), 70)]
        for chunk in text_chunks[:80]:  # More text per page
            if y_position < 50:
                break
            c.drawString(50, y_position, chunk)
            y_position -= 10

        # Add some images to increase file size
        if page % 5 == 0:  # Every 5th page
            from reportlab.lib.utils import ImageReader
            from PIL import Image as PILImage
            import io as image_io

            # Create a larger image
            img = PILImage.new("RGB", (200, 200), color="blue")
            img_buffer = image_io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            # Add the image to the PDF
            c.drawImage(ImageReader(img_buffer), 400, 400, width=100, height=100)

        c.showPage()

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def create_font_size_test_pdf(
    small_font: int = 6, large_font: int = 24, include_normal: bool = True
) -> bytes:
    """Create a PDF with various font sizes for testing.

    Args:
        small_font: Small font size (should be < MIN_FONT)
        large_font: Large font size (should be > MAX_FONT)
        include_normal: Whether to include normal-sized text

    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setAuthor("Test Author")
    c.setTitle("Font Size Test PDF")

    y_position = letter[1] - 100

    # Add small font text
    c.setFont("Helvetica", small_font)
    c.drawString(100, y_position, f"This text is {small_font}pt (too small)")
    y_position -= 50

    # Add large font text
    c.setFont("Helvetica", large_font)
    c.drawString(100, y_position, f"This text is {large_font}pt (too large)")
    y_position -= 50

    # Add normal font text if requested
    if include_normal:
        c.setFont("Helvetica", 12)
        c.drawString(100, y_position, "This text is 12pt (normal)")

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def create_colored_pdf(use_saturated_colors: bool = True) -> bytes:
    """Create a PDF with colored elements.

    Args:
        use_saturated_colors: Whether to use saturated colors (non-grayscale)

    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setAuthor("Test Author")
    c.setTitle("Colored Test PDF")

    if use_saturated_colors:
        # Use bright red background
        c.setFillColor(red)
        c.rect(0, 0, letter[0], letter[1], fill=1)

        # Blue text
        c.setFillColor(blue)
    else:
        # Use grayscale colors
        gray_bg = Color(0.9, 0.9, 0.9)  # Light gray
        c.setFillColor(gray_bg)
        c.rect(0, 0, letter[0], letter[1], fill=1)

        # Dark gray text
        c.setFillColor(Color(0.2, 0.2, 0.2))

    c.setFont("Helvetica", 12)
    c.drawString(100, letter[1] - 100, "This PDF has colored elements")

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def create_pdf_with_spelling_errors() -> bytes:
    """Create a PDF with intentional spelling errors.

    Returns:
        PDF content as bytes
    """
    # Text with spelling errors
    text_with_errors = """
    This is a sampel CV with some mispelled words.
    I have experiance in sofware development.
    My skils include programing and databse management.
    I am very entusiastic about tecnology.
    """

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setAuthor("Test Author")
    c.setTitle("Spelling Test PDF")

    c.setFont("Helvetica", 12)
    y_position = letter[1] - 100

    # Split text into lines and add to PDF
    lines = text_with_errors.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line:
            c.drawString(100, y_position, line)
            y_position -= 20

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def create_pdf_without_metadata() -> bytes:
    """Create a PDF without proper metadata.

    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Explicitly set empty metadata
    c.setAuthor("")
    c.setTitle("")
    c.setSubject("")
    c.setCreator("")

    c.setFont("Helvetica", 12)
    c.drawString(100, letter[1] - 100, "This PDF has no metadata")

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def create_temp_pdf_file(pdf_bytes: bytes) -> str:
    """Create a temporary PDF file from bytes.

    Args:
        pdf_bytes: PDF content as bytes

    Returns:
        Path to temporary PDF file
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_bytes)
        return tmp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """Clean up a temporary file.

    Args:
        file_path: Path to file to delete
    """
    try:
        os.unlink(file_path)
    except (OSError, FileNotFoundError):
        pass  # File already deleted or doesn't exist
