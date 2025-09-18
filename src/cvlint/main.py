from dataclasses import dataclass
from typing import Callable, List
from pypdf import PdfReader
from spellchecker import SpellChecker
from pathlib import Path
import re
import pytest
import fitz
from PIL import Image
import colorsys
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar

@dataclass
class Criterion:
    name: str
    description: str
    check_func: Callable[[str], bool]  # receives resume text or parsed data, returns True/False
    weight: float # how many points this criterion is worth

# ---------- Configuration ----------
PDF_PATH = Path(".")
MAX_PAGES : int = 1  # Max number of pages allowed in the PDF
MIN_FONT : int = 8  # Minimum font size allowed in points
MAX_FONT : int = 21  # aximum font size allowed in points
ENFORCE_HTTPS : bool = True  # Require all links to use HTTPS (all links validated anyway)
MAX_FILE_SIZE_KB : float = 500  # Max allowed PDF file size in kilobytes
NO_IMAGES : bool = True  # PDF must contain no images if True
MAX_COLORS : int = 1  # TODO: Max number of unique colors/hues allowed
BACKGROUND_WHITE : bool = True  # PDF background must be white if True
GRAYSCALE_COLORS : bool = True  # PDF colors must be grayscale only if True
CUSTOM_WORDS : List[str] = []

# ---------- Criteria List ----------
def create_criteria_list() -> List[Criterion]:
    """Create a list of all CV validation criteria."""
    return [
        Criterion(
            name="PDF File Exists",
            description="Validates that the CV PDF file exists at the specified path",
            check_func=lambda _: test_pdf_exists_wrapper(),
            weight=10.0
        ),
        Criterion(
            name="Single Page Limit",
            description="Ensures the CV is exactly one page or less",
            check_func=lambda _: test_pdf_page_count_wrapper(),
            weight=15.0
        ),
        Criterion(
            name="File Size Constraint",
            description=f"Validates that the PDF file size is within {MAX_FILE_SIZE_KB}KB limit",
            check_func=lambda _: test_pdf_file_size_wrapper(),
            weight=8.0
        ),
        Criterion(
            name="Font Size Range",
            description=f"Ensures all fonts are between {MIN_FONT}pt and {MAX_FONT}pt",
            check_func=lambda _: test_pdf_font_sizes_wrapper(),
            weight=12.0
        ),
        Criterion(
            name="HTTPS Links Only",
            description="Validates that all links in the PDF use HTTPS protocol",
            check_func=lambda _: test_pdf_links_https_wrapper(),
            weight=7.0
        ),
        Criterion(
            name="No Embedded Images",
            description="Ensures the PDF contains no embedded images",
            check_func=lambda _: test_pdf_no_images_wrapper(),
            weight=5.0
        ),
        Criterion(
            name="White Background",
            description="Validates that the PDF has a white background",
            check_func=lambda _: test_pdf_background_white_wrapper(),
            weight=6.0
        ),
        Criterion(
            name="Grayscale Colors Only",
            description="Ensures all colors in the PDF are grayscale (no saturation)",
            check_func=lambda _: test_pdf_all_pixels_no_saturation_wrapper(),
            weight=8.0
        ),
        Criterion(
            name="Spell Check and Capitalization",
            description="Validates spelling and proper capitalization of technical terms",
            check_func=lambda _: test_pdf_spell_check_wrapper(),
            weight=20.0
        ),
        Criterion(
            name="PDF Structure and Metadata",
            description="Validates PDF metadata (author, title) and text readability",
            check_func=lambda _: test_pdf_structure_wrapper(),
            weight=9.0
        ),
        Criterion(
            name="PDF Integrity",
            description="Ensures the PDF is not corrupted and can be properly read",
            check_func=lambda _: test_pdf_not_corrupted_wrapper(),
            weight=10.0
        )
    ]

# Wrapper functions to convert test functions to boolean returns
def test_pdf_exists_wrapper() -> bool:
    try:
        test_pdf_exists()
        return True
    except AssertionError:
        return False

def test_pdf_page_count_wrapper() -> bool:
    try:
        test_pdf_page_count()
        return True
    except AssertionError:
        return False

def test_pdf_file_size_wrapper() -> bool:
    try:
        test_pdf_file_size()
        return True
    except AssertionError:
        return False

def test_pdf_font_sizes_wrapper() -> bool:
    try:
        test_pdf_font_sizes()
        return True
    except AssertionError:
        return False

def test_pdf_links_https_wrapper() -> bool:
    try:
        test_pdf_links_https()
        return True
    except (AssertionError, pytest.skip.Exception):
        return False

def test_pdf_no_images_wrapper() -> bool:
    try:
        test_pdf_no_images()
        return True
    except (AssertionError, pytest.skip.Exception):
        return False

def test_pdf_background_white_wrapper() -> bool:
    try:
        test_pdf_background_white()
        return True
    except (AssertionError, pytest.skip.Exception):
        return False

def test_pdf_all_pixels_no_saturation_wrapper() -> bool:
    try:
        test_pdf_all_pixels_no_saturation()
        return True
    except (AssertionError, pytest.skip.Exception):
        return False

def test_pdf_spell_check_wrapper() -> bool:
    try:
        test_pdf_spell_check()
        return True
    except AssertionError:
        return False

def test_pdf_structure_wrapper() -> bool:
    try:
        test_pdf_structure()
        return True
    except AssertionError:
        return False

def test_pdf_not_corrupted_wrapper() -> bool:
    try:
        test_pdf_not_corrupted()
        return True
    except AssertionError:
        return False

# ---------- PDF Tests ----------
def test_pdf_exists():
    assert PDF_PATH.is_file(), f"CV PDF not found at {PDF_PATH}"


def test_pdf_page_count():
    pdf = PdfReader(PDF_PATH)
    assert len(pdf.pages) <= 1, f"CV is {len(pdf.pages)} pages (should be ≤1 page)"


def test_pdf_file_size():
    """Test that the PDF file size is within the specified limit."""
    file_size_kb = PDF_PATH.stat().st_size / 1024
    assert (
        file_size_kb <= MAX_FILE_SIZE_KB
    ), f"CV file size is {file_size_kb:.1f}KB (should be ≤{MAX_FILE_SIZE_KB}KB)"


def test_pdf_font_sizes(min_size=MIN_FONT, max_size=MAX_FONT):
    """Test that all fonts in the PDF are within the specified size range."""
    errors = []

    for page_layout in extract_pages(PDF_PATH):
        page_num = page_layout.pageid
        for element in page_layout:
            if isinstance(element, (LTTextBox, LTTextLine)):
                bad_chars = []
                bad_sizes = []
                for text_line in element:
                    for char in text_line:
                        if isinstance(char, LTChar):
                            font_size = char.size
                            if font_size < min_size or font_size > max_size:
                                bad_chars.append(char.get_text())
                                bad_sizes.append(font_size)

                if bad_chars:
                    bad_text = "".join(bad_chars).strip()
                    # Find whether too small or too big, or both in the same snippet
                    too_small = any(size < min_size for size in bad_sizes)
                    too_big = any(size > max_size for size in bad_sizes)

                    size_status = []
                    if too_small:
                        size_status.append(f"smaller than minimum {min_size}")
                    if too_big:
                        size_status.append(f"larger than maximum {max_size}")
                    size_status_str = " and ".join(size_status)

                    errors.append(
                        f"Page {page_num}: Text with font size {size_status_str}: '{bad_text}'"
                    )

    if errors:
        raise AssertionError("\n".join(errors))


def test_pdf_links_https():
    """Test that all links in the PDF use HTTPS when ENFORCE_HTTPS is True."""
    if not ENFORCE_HTTPS:
        pytest.skip("HTTPS enforcement is disabled")

    pdf = PdfReader(PDF_PATH)
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
        assert link.startswith("https://"), f"Link '{link}' does not use HTTPS"


def test_pdf_no_images():
    """Test that the PDF contains no images when NO_IMAGES is True."""
    if not NO_IMAGES:
        pytest.skip("Image checking is disabled")

    pdf = PdfReader(PDF_PATH)

    for page_num, page in enumerate(pdf.pages):
        if "/XObject" in page.get("/Resources", {}):
            xobjects = page["/Resources"]["/XObject"]
            for obj_name in xobjects:
                obj = xobjects[obj_name]
                if obj.get("/Subtype") == "/Image":
                    assert (
                        False
                    ), f"Found image '{obj_name}' on page {page_num + 1}, but NO_IMAGES is True"


def test_pdf_background_white():
    """Test that the PDF has a white background when BACKGROUND_WHITE is True."""
    if not BACKGROUND_WHITE:
        pytest.skip("Background color checking is disabled")

    doc = fitz.open(PDF_PATH)
    page = doc[0]
    pix = page.get_pixmap(alpha=False)

    r, g, b = pix.pixel(0, 0)
    doc.close()

    assert (r, g, b) == (
        255,
        255,
        255,
    ), f"Expected white background, got RGB({r}, {g}, {b})"


def rgb_to_hsv(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h, s, v


def test_pdf_all_pixels_no_saturation(tolerance=0.01):

    if not GRAYSCALE_COLORS:
        pytest.skip("Grayscale color checking is disabled")
    """Test that every pixel in the PDF has saturation <= tolerance (i.e., grayscale)."""
    doc = fitz.open(PDF_PATH)

    for page_num, page in enumerate(doc, start=1):
        pix = page.get_pixmap(alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pixels = image.getdata()

        for i, pixel in enumerate(pixels):
            _, s, _ = rgb_to_hsv(pixel)
            if s > tolerance:
                doc.close()
                raise AssertionError(
                    f"Pixel with saturation {s:.3f} found on page {page_num} at pixel index {i}"
                )

    doc.close()
    print("All pixels have zero (or near zero) saturation — PDF is grayscale.")


def test_pdf_spell_check():
    """Test that the PDF text passes spell checking with custom words and capitalization rules."""
    pdf = PdfReader(PDF_PATH)
    spell = SpellChecker()

    # Build allowed word variations based on capitalization rules
    allowed_words = set()
    capitalization_errors = []

    for custom_word in CUSTOM_WORDS:
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

        # Check if word is in our allowed set or standard dictionary
        if word in allowed_words or spell.known([word]):
            continue

        # Check for capitalization errors in custom words
        found_capitalization_error = False
        for custom_word in CUSTOM_WORDS:
            if word.lower() == custom_word.lower() and word != custom_word:
                # If custom word is not all lowercase, it has specific capitalization requirements
                if not custom_word.islower():
                    capitalization_errors.append(
                        f"Found '{word}' but should be '{custom_word}'"
                    )
                    found_capitalization_error = True
                    break

        if not found_capitalization_error:
            # Additional filtering for likely valid words
            if word.lower().startswith(".") or word.lower().endswith("."):
                continue
            if any(tech in word.lower() for tech in ["js", "sql", "xml", "json"]):
                continue

            actual_misspelled.append(word)

    # Remove duplicates while preserving order
    actual_misspelled = list(dict.fromkeys(actual_misspelled))

    # Report both spelling and capitalization errors
    all_errors = []
    if actual_misspelled:
        all_errors.append(f"Misspelled words: {actual_misspelled}")
    if capitalization_errors:
        all_errors.append(f"Capitalization errors: {capitalization_errors}")

    assert len(all_errors) == 0, "; ".join(all_errors)


def test_pdf_structure():
    """Test basic PDF structure and readability."""
    pdf = PdfReader(PDF_PATH)

    # Test that PDF has metadata
    metadata = pdf.metadata
    assert metadata is not None, "PDF should have metadata"

    author = metadata.get("/Author")
    assert (
        author is not None and author.strip() != ""
    ), "PDF should have a valid Author metadata field"

    title = metadata.get("/Title")
    assert (
        title is not None and title.strip() != ""
    ), "PDF should have a valid Title metadata field"

    # Test that we can extract text from all pages
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        assert (
            len(text.strip()) > 0
        ), f"Page {page_num + 1} should contain readable text"


def test_pdf_not_corrupted():
    """Test that the PDF is not corrupted and can be properly read."""
    try:
        pdf = PdfReader(PDF_PATH)
        # Try to access all pages
        for page in pdf.pages:
            page.extract_text()
        assert True
    except Exception as e:
        assert False, f"PDF appears to be corrupted: {e}"
