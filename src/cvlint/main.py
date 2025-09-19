from dataclasses import dataclass
from typing import Callable, List, Optional
from pypdf import PdfReader
from spellchecker import SpellChecker
from pathlib import Path
import re
import fitz
from PIL import Image
import colorsys
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar


@dataclass
class Criterion:
    name: str
    description: str
    check_func: Callable[..., bool]  # receives parameters, returns True/False
    weight: float  # how many points this criterion is worth


@dataclass
class ValidationConfig:
    pdf_path: Path
    max_pages: int = 1
    max_file_size_kb: float = 500
    min_font: int = 8
    max_font: int = 21
    enforce_https: bool = True
    no_images: bool = True
    background_white: bool = True
    grayscale_colors: bool = True
    custom_words: List[str] = None

    def __post_init__(self):
        if self.custom_words is None:
            self.custom_words = []


# ---------- Criteria List ----------
def create_criteria_list(config: ValidationConfig) -> List[Criterion]:
    """Create a list of all CV validation criteria."""
    return [
        Criterion(
            name="PDF File Exists",
            description="Validates that the CV PDF file exists at the specified path",
            check_func=lambda: check_pdf_exists(config.pdf_path),
            weight=10.0,
        ),
        Criterion(
            name="Single Page Limit",
            description="Ensures the CV is exactly one page or less",
            check_func=lambda: check_pdf_page_count(config.pdf_path, config.max_pages),
            weight=15.0,
        ),
        Criterion(
            name="File Size Constraint",
            description=f"Validates that the PDF file size is within {config.max_file_size_kb}KB limit",
            check_func=lambda: check_pdf_file_size(
                config.pdf_path, config.max_file_size_kb
            ),
            weight=8.0,
        ),
        Criterion(
            name="Font Size Range",
            description=f"Ensures all fonts are between {config.min_font}pt and {config.max_font}pt",
            check_func=lambda: check_pdf_font_sizes(
                config.pdf_path, config.min_font, config.max_font
            ),
            weight=12.0,
        ),
        Criterion(
            name="HTTPS Links Only",
            description="Validates that all links in the PDF use HTTPS protocol",
            check_func=lambda: check_pdf_links_https(
                config.pdf_path, config.enforce_https
            ),
            weight=7.0,
        ),
        Criterion(
            name="No Embedded Images",
            description="Ensures the PDF contains no embedded images",
            check_func=lambda: check_pdf_no_images(config.pdf_path, config.no_images),
            weight=5.0,
        ),
        Criterion(
            name="White Background",
            description="Validates that the PDF has a white background",
            check_func=lambda: check_pdf_background_white(
                config.pdf_path, config.background_white
            ),
            weight=6.0,
        ),
        Criterion(
            name="Grayscale Colors Only",
            description="Ensures all colors in the PDF are grayscale (no saturation)",
            check_func=lambda: check_pdf_all_pixels_no_saturation(
                config.pdf_path, config.grayscale_colors
            ),
            weight=8.0,
        ),
        Criterion(
            name="Spell Check and Capitalization",
            description="Validates spelling and proper capitalization of technical terms",
            check_func=lambda: check_pdf_spell_check(
                config.pdf_path, config.custom_words
            ),
            weight=20.0,
        ),
        Criterion(
            name="PDF Structure and Metadata",
            description="Validates PDF metadata (author, title) and text readability",
            check_func=lambda: check_pdf_structure(config.pdf_path),
            weight=9.0,
        ),
        Criterion(
            name="PDF Integrity",
            description="Ensures the PDF is not corrupted and can be properly read",
            check_func=lambda: check_pdf_not_corrupted(config.pdf_path),
            weight=10.0,
        ),
    ]


# ---------- PDF Checks ----------
def check_pdf_exists(pdf_path: Path) -> bool:
    """Check that the CV PDF file exists at the specified path."""
    return pdf_path.is_file()


def check_pdf_page_count(pdf_path: Path, max_pages: int) -> bool:
    """Check that the CV is exactly one page or less."""
    try:
        pdf = PdfReader(pdf_path)
        return len(pdf.pages) <= max_pages
    except Exception:
        return False


def check_pdf_file_size(pdf_path: Path, max_file_size_kb: float) -> bool:
    """Check that the PDF file size is within the specified limit."""
    try:
        file_size_kb = pdf_path.stat().st_size / 1024
        return file_size_kb <= max_file_size_kb
    except Exception:
        return False


def check_pdf_font_sizes(pdf_path: Path, min_size: int, max_size: int) -> bool:
    """Test that all fonts in the PDF are within the specified size range."""
    try:
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, (LTTextBox, LTTextLine)):
                    for text_line in element:
                        for char in text_line:
                            if isinstance(char, LTChar):
                                font_size = char.size
                                if font_size < min_size or font_size > max_size:
                                    return False
        return True
    except Exception:
        return False


def check_pdf_links_https(pdf_path: Path, enforce_https: bool) -> bool:
    """Check that all links in the PDF use HTTPS when enforce_https is True."""
    if not enforce_https:
        return True  # Skip check if HTTPS enforcement is disabled

    try:
        pdf = PdfReader(pdf_path)
        links = []

        for page in pdf.pages:
            if "/Annots" in page:
                annotations = page["/Annots"]
                for annotation in annotations:
                    annotation_obj = annotation.get_object()
                    if "/A" in annotation_obj and "/URI" in annotation_obj["/A"]:
                        uri = annotation_obj["/A"]["/URI"]
                        links.append(uri)

        for link in links:
            if not link.startswith("https://"):
                return False

        return True
    except Exception:
        return False


def check_pdf_no_images(pdf_path: Path, no_images: bool) -> bool:
    """Check that the PDF contains no images when no_images is True."""
    if not no_images:
        return True  # Skip check if image checking is disabled

    try:
        pdf = PdfReader(pdf_path)

        for page_num, page in enumerate(pdf.pages):
            if "/XObject" in page.get("/Resources", {}):
                xobjects = page["/Resources"]["/XObject"]
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    if obj.get("/Subtype") == "/Image":
                        return False

        return True
    except Exception:
        return False


def check_pdf_background_white(pdf_path: Path, background_white: bool) -> bool:
    """Check that the PDF has a white background when background_white is True."""
    if not background_white:
        return True  # Skip check if background color checking is disabled

    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(alpha=False)

        r, g, b = pix.pixel(0, 0)
        doc.close()

        return (r, g, b) == (255, 255, 255)
    except Exception:
        return False


def rgb_to_hsv(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h, s, v


def check_pdf_all_pixels_no_saturation(
    pdf_path: Path, grayscale_colors: bool, tolerance: float = 0.01
) -> bool:
    """Check that every pixel in the PDF has saturation <= tolerance (i.e., grayscale)."""
    if not grayscale_colors:
        return True  # Skip check if grayscale color checking is disabled

    try:
        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc, start=1):
            pix = page.get_pixmap(alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pixels = image.getdata()

            for i, pixel in enumerate(pixels):
                _, s, _ = rgb_to_hsv(pixel)
                if s > tolerance:
                    doc.close()
                    return False

        doc.close()
        return True
    except Exception:
        return False


def check_pdf_spell_check(pdf_path: Path, custom_words: List[str]) -> bool:
    """Check that the PDF text passes spell checking with custom words and capitalization rules."""
    try:
        pdf = PdfReader(pdf_path)
        spell = SpellChecker()

        # Build allowed word variations based on capitalization rules
        allowed_words = set()
        capitalization_errors = []

        for custom_word in custom_words:
            if custom_word.islower():
                # All lowercase words allow both lowercase and first-letter capitalization
                allowed_words.add(custom_word)
                allowed_words.add(custom_word.capitalize())
            else:
                # Words with specific capitalization must appear exactly as defined
                allowed_words.add(custom_word)

        # Also add standard dictionary words
        spell.word_frequency.load_words(allowed_words)

        # Extract all text from the PDF
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()

        # Extract words preserving original case
        original_words = re.findall(r"\b[a-zA-Z]+\b", full_text)

        # Check each word for spelling and capitalization
        actual_misspelled = []
        for word in original_words:
            # Skip very short words (likely abbreviations)
            if len(word) < 3:
                continue
            # Skip single letters
            if len(word) == 1:
                continue

            # Check for capitalization errors in custom words FIRST
            found_capitalization_error = False
            for custom_word in custom_words:
                if word.lower() == custom_word.lower() and word != custom_word:
                    # If custom word is not all lowercase, it has specific capitalization requirements
                    if not custom_word.islower():
                        capitalization_errors.append(
                            f"Found '{word}' but should be '{custom_word}'"
                        )
                        found_capitalization_error = True
                        break

            # If we found a capitalization error, this word is an error - don't process further
            if found_capitalization_error:
                continue

            # Check if word is in our allowed set or standard dictionary
            if word in allowed_words or spell.known([word]):
                continue

            # Additional filtering for likely valid words (only for non-capitalization errors)
            if word.lower().startswith(".") or word.lower().endswith("."):
                continue
            if any(tech in word.lower() for tech in ["js", "sql", "xml", "json"]):
                continue
            # Skip common URL terms
            if word.lower() in ["https", "http", "www", "com", "org", "net"]:
                continue
            # Skip words that are part of URLs or email addresses
            if any(
                url_part in word.lower()
                for url_part in ["github", "linkedin", "gmail", "yahoo", "hotmail"]
            ):
                continue

            actual_misspelled.append(word)

        # Remove duplicates while preserving order
        actual_misspelled = list(dict.fromkeys(actual_misspelled))

        # Return False if there are any spelling or capitalization errors
        return len(actual_misspelled) == 0 and len(capitalization_errors) == 0
    except Exception:
        return False


def check_pdf_structure(pdf_path: Path) -> bool:
    """Check basic PDF structure and readability."""
    try:
        pdf = PdfReader(pdf_path)

        # Test that PDF has metadata
        metadata = pdf.metadata
        if metadata is None:
            return False

        author = metadata.get("/Author")
        if author is None or author.strip() == "":
            return False

        title = metadata.get("/Title")
        if title is None or title.strip() == "":
            return False

        # Test that we can extract text from all pages
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if len(text.strip()) == 0:
                return False

        return True
    except Exception:
        return False


def check_pdf_not_corrupted(pdf_path: Path) -> bool:
    """Check that the PDF is not corrupted and can be properly read."""
    try:
        pdf = PdfReader(pdf_path)
        # Try to access all pages
        for page in pdf.pages:
            page.extract_text()
        return True
    except Exception:
        return False
