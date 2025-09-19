"""Pytest configuration and fixtures for cvlint tests."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from tests.utils import (
    create_basic_pdf,
    create_large_pdf,
    create_font_size_test_pdf,
    create_colored_pdf,
    create_pdf_with_spelling_errors,
    create_pdf_without_metadata,
    create_temp_pdf_file,
    cleanup_temp_file,
)
from reportlab.lib.colors import red, blue, Color


@pytest.fixture
def temp_pdf_dir():
    """Create a temporary directory for PDF files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def valid_pdf():
    """Create a valid PDF that should pass all checks."""
    pdf_bytes = create_basic_pdf(
        text="This is a valid CV with proper content.",
        font_size=12,
        pages=1,
        author="John Doe",
        title="John Doe CV",
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def multi_page_pdf():
    """Create a PDF with multiple pages."""
    pdf_bytes = create_basic_pdf(
        text="This CV has multiple pages",
        pages=3,
        author="Test Author",
        title="Multi-page CV",
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def large_pdf():
    """Create a PDF that exceeds size limits."""
    pdf_bytes = create_large_pdf(target_size_kb=600)
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def small_font_pdf():
    """Create a PDF with fonts that are too small."""
    pdf_bytes = create_font_size_test_pdf(
        small_font=6,  # Below MIN_FONT (8)
        large_font=12,  # Normal size
        include_normal=True,
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def large_font_pdf():
    """Create a PDF with fonts that are too large."""
    pdf_bytes = create_font_size_test_pdf(
        small_font=12,  # Normal size
        large_font=24,  # Above MAX_FONT (21)
        include_normal=True,
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def http_link_pdf():
    """Create a PDF with HTTP (non-HTTPS) links."""
    pdf_bytes = create_basic_pdf(
        text="CV with HTTP link",
        add_link="http://example.com",
        author="Test Author",
        title="HTTP Link CV",
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def https_link_pdf():
    """Create a PDF with HTTPS links."""
    pdf_bytes = create_basic_pdf(
        text="CV with HTTPS link",
        add_link="https://example.com",
        author="Test Author",
        title="HTTPS Link CV",
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def pdf_with_image():
    """Create a PDF with embedded images."""
    pdf_bytes = create_basic_pdf(
        text="CV with image", add_image=True, author="Test Author", title="Image CV"
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def colored_background_pdf():
    """Create a PDF with non-white background."""
    pdf_bytes = create_basic_pdf(
        text="CV with colored background",
        background_color=red,
        author="Test Author",
        title="Colored Background CV",
    )
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def saturated_colors_pdf():
    """Create a PDF with saturated (non-grayscale) colors."""
    pdf_bytes = create_colored_pdf(use_saturated_colors=True)
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def grayscale_pdf():
    """Create a PDF with only grayscale colors."""
    pdf_bytes = create_colored_pdf(use_saturated_colors=False)
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def spelling_errors_pdf():
    """Create a PDF with spelling errors."""
    pdf_bytes = create_pdf_with_spelling_errors()
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def no_metadata_pdf():
    """Create a PDF without proper metadata."""
    pdf_bytes = create_pdf_without_metadata()
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)


@pytest.fixture
def corrupted_pdf():
    """Create a corrupted PDF."""
    pdf_bytes = create_basic_pdf(corrupt=True)
    temp_file = create_temp_pdf_file(pdf_bytes)
    yield temp_file
    cleanup_temp_file(temp_file)
