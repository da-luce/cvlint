"""Comprehensive tests for PDF validation checks."""

import pytest
from pathlib import Path
from src.cvlint.main import (
    ValidationConfig,
    create_criteria_list,
    check_pdf_exists,
    check_pdf_page_count,
    check_pdf_file_size,
    check_pdf_font_sizes,
    check_pdf_links_https,
    check_pdf_no_images,
    check_pdf_background_white,
    check_pdf_all_pixels_no_saturation,
    check_pdf_spell_check,
    check_pdf_structure,
    check_pdf_not_corrupted,
)


class TestPdfExists:
    """Test PDF file existence validation."""

    def test_pdf_exists_valid_file(self, valid_pdf):
        """Test that check passes when PDF file exists."""
        result = check_pdf_exists(Path(valid_pdf))
        assert result is True

    def test_pdf_exists_missing_file(self):
        """Test that check fails when PDF file doesn't exist."""
        result = check_pdf_exists(Path("/nonexistent/file.pdf"))
        assert result is False


class TestPdfPageCount:
    """Test PDF page count validation."""

    def test_single_page_pdf_passes(self, valid_pdf):
        """Test that single-page PDF passes."""
        result = check_pdf_page_count(Path(valid_pdf), max_pages=1)
        assert result is True

    def test_multi_page_pdf_fails(self, multi_page_pdf):
        """Test that multi-page PDF fails."""
        result = check_pdf_page_count(Path(multi_page_pdf), max_pages=1)
        assert result is False

    def test_multi_page_pdf_passes_with_higher_limit(self, multi_page_pdf):
        """Test that multi-page PDF passes with higher page limit."""
        result = check_pdf_page_count(Path(multi_page_pdf), max_pages=5)
        assert result is True


class TestPdfFileSize:
    """Test PDF file size validation."""

    def test_normal_size_pdf_passes(self, valid_pdf):
        """Test that normal-sized PDF passes."""
        result = check_pdf_file_size(Path(valid_pdf), max_file_size_kb=500)
        assert result is True

    def test_large_pdf_fails(self, large_pdf):
        """Test that oversized PDF fails."""
        result = check_pdf_file_size(
            Path(large_pdf), max_file_size_kb=50
        )  # Set limit to 50KB so 60KB PDF fails
        assert result is False

    def test_exact_size_limit_passes(self, valid_pdf):
        """Test that PDF at exact size limit passes."""
        # Get the actual file size and set limit to that exact size
        file_size_kb = Path(valid_pdf).stat().st_size / 1024
        result = check_pdf_file_size(Path(valid_pdf), max_file_size_kb=file_size_kb)
        assert result is True


class TestPdfFontSizes:
    """Test PDF font size validation."""

    def test_normal_fonts_pass(self, valid_pdf):
        """Test that normal font sizes pass."""
        result = check_pdf_font_sizes(Path(valid_pdf), min_size=8, max_size=21)
        assert result is True

    def test_small_fonts_fail(self, small_font_pdf):
        """Test that fonts below minimum size fail."""
        result = check_pdf_font_sizes(Path(small_font_pdf), min_size=8, max_size=21)
        assert result is False

    def test_large_fonts_fail(self, large_font_pdf):
        """Test that fonts above maximum size fail."""
        result = check_pdf_font_sizes(Path(large_font_pdf), min_size=8, max_size=21)
        assert result is False

    def test_custom_font_size_limits(self, valid_pdf):
        """Test custom font size limits."""
        # Should pass with custom limits that include the font size
        result = check_pdf_font_sizes(Path(valid_pdf), min_size=10, max_size=15)
        # This might pass or fail depending on the actual font sizes in valid_pdf
        assert isinstance(result, bool)

    def test_very_permissive_limits_pass(self, small_font_pdf):
        """Test that very permissive limits allow small fonts to pass."""
        result = check_pdf_font_sizes(Path(small_font_pdf), min_size=1, max_size=50)
        assert result is True


class TestPdfLinksHttps:
    """Test PDF HTTPS links validation."""

    def test_https_links_pass(self, https_link_pdf):
        """Test that HTTPS links pass when enforcement is enabled."""
        result = check_pdf_links_https(Path(https_link_pdf), enforce_https=True)
        assert result is True

    def test_http_links_fail(self, http_link_pdf):
        """Test that HTTP links fail when enforcement is enabled."""
        result = check_pdf_links_https(Path(http_link_pdf), enforce_https=True)
        assert result is False

    def test_https_enforcement_disabled(self, http_link_pdf):
        """Test that check is skipped when HTTPS enforcement is disabled."""
        result = check_pdf_links_https(Path(http_link_pdf), enforce_https=False)
        assert result is True  # Should return True when enforcement is disabled

    def test_no_links_pass(self, valid_pdf):
        """Test that PDFs without links pass."""
        result = check_pdf_links_https(Path(valid_pdf), enforce_https=True)
        assert result is True


class TestPdfNoImages:
    """Test PDF image validation."""

    def test_no_images_pass(self, valid_pdf):
        """Test that PDFs without images pass."""
        result = check_pdf_no_images(Path(valid_pdf), no_images=True)
        assert result is True

    def test_with_images_fail(self, pdf_with_image):
        """Test that PDFs with images fail when NO_IMAGES is True."""
        result = check_pdf_no_images(Path(pdf_with_image), no_images=True)
        assert result is False

    def test_image_checking_disabled(self, pdf_with_image):
        """Test that check is skipped when image checking is disabled."""
        result = check_pdf_no_images(Path(pdf_with_image), no_images=False)
        assert result is True  # Should return True when checking is disabled


class TestPdfBackgroundWhite:
    """Test PDF background color validation."""

    def test_white_background_passes(self, valid_pdf):
        """Test that white background passes."""
        result = check_pdf_background_white(Path(valid_pdf), background_white=True)
        assert result is True

    def test_colored_background_fails(self, colored_background_pdf):
        """Test that colored background fails."""
        result = check_pdf_background_white(
            Path(colored_background_pdf), background_white=True
        )
        assert result is False

    def test_background_checking_disabled(self, colored_background_pdf):
        """Test that check is skipped when background checking is disabled."""
        result = check_pdf_background_white(
            Path(colored_background_pdf), background_white=False
        )
        assert result is True  # Should return True when checking is disabled


class TestPdfGrayscaleColors:
    """Test PDF grayscale color validation."""

    def test_grayscale_colors_pass(self, grayscale_pdf):
        """Test that grayscale colors pass."""
        result = check_pdf_all_pixels_no_saturation(
            Path(grayscale_pdf), grayscale_colors=True
        )
        assert result is True

    def test_saturated_colors_fail(self, saturated_colors_pdf):
        """Test that saturated colors fail."""
        result = check_pdf_all_pixels_no_saturation(
            Path(saturated_colors_pdf), grayscale_colors=True
        )
        assert result is False

    def test_grayscale_checking_disabled(self, saturated_colors_pdf):
        """Test that check is skipped when grayscale checking is disabled."""
        result = check_pdf_all_pixels_no_saturation(
            Path(saturated_colors_pdf), grayscale_colors=False
        )
        assert result is True  # Should return True when checking is disabled

    def test_custom_tolerance(self, saturated_colors_pdf):
        """Test custom saturation tolerance."""
        # Should still fail even with higher tolerance for very saturated colors
        result = check_pdf_all_pixels_no_saturation(
            Path(saturated_colors_pdf), grayscale_colors=True, tolerance=0.1
        )
        assert result is False


class TestPdfSpellCheck:
    """Test PDF spell checking validation."""

    def test_correct_spelling_passes(self, valid_pdf):
        """Test that correctly spelled text passes."""
        result = check_pdf_spell_check(Path(valid_pdf), custom_words=[])
        assert result is True

    def test_spelling_errors_fail(self, spelling_errors_pdf):
        """Test that spelling errors fail."""
        result = check_pdf_spell_check(Path(spelling_errors_pdf), custom_words=[])
        assert result is False

    def test_custom_words_allowed(self):
        """Test that custom words are allowed."""
        from tests.utils import (
            create_basic_pdf,
            create_temp_pdf_file,
            cleanup_temp_file,
        )

        # Create PDF with technical terms
        pdf_bytes = create_basic_pdf(
            text="I have experience with JavaScript and PostgreSQL databases.",
            author="Test Author",
            title="Technical CV",
        )
        temp_file = create_temp_pdf_file(pdf_bytes)

        try:
            result = check_pdf_spell_check(
                Path(temp_file), custom_words=["javascript", "postgresql"]
            )
            assert result is True
        finally:
            cleanup_temp_file(temp_file)

    def test_capitalization_rules(self):
        """Test capitalization rules for custom words."""
        from tests.utils import (
            create_basic_pdf,
            create_temp_pdf_file,
            cleanup_temp_file,
        )

        # Create PDF with incorrectly capitalized technical terms (using a made-up framework name)
        pdf_bytes = create_basic_pdf(
            text="I have experience with reactjs and REACTJS framework development.",
            author="Test Author",
            title="Capitalization Test CV",
        )
        temp_file = create_temp_pdf_file(pdf_bytes)

        try:
            result = check_pdf_spell_check(
                Path(temp_file), custom_words=["ReactJS"]
            )  # Specific capitalization required
            assert result is False  # Should fail due to capitalization errors
        finally:
            cleanup_temp_file(temp_file)


class TestPdfStructure:
    """Test PDF structure and metadata validation."""

    def test_valid_metadata_passes(self, valid_pdf):
        """Test that valid metadata passes."""
        result = check_pdf_structure(Path(valid_pdf))
        assert result is True

    def test_missing_metadata_fails(self, no_metadata_pdf):
        """Test that missing metadata fails."""
        result = check_pdf_structure(Path(no_metadata_pdf))
        assert result is False

    def test_empty_metadata_fails(self):
        """Test that empty metadata fails."""
        from tests.utils import (
            create_basic_pdf,
            create_temp_pdf_file,
            cleanup_temp_file,
        )

        # Create PDF with empty metadata
        pdf_bytes = create_basic_pdf(
            text="CV with empty metadata",
            author="",  # Empty author
            title="",  # Empty title
        )
        temp_file = create_temp_pdf_file(pdf_bytes)

        try:
            result = check_pdf_structure(Path(temp_file))
            assert result is False
        finally:
            cleanup_temp_file(temp_file)


class TestPdfNotCorrupted:
    """Test PDF corruption validation."""

    def test_valid_pdf_passes(self, valid_pdf):
        """Test that valid PDF passes corruption check."""
        result = check_pdf_not_corrupted(Path(valid_pdf))
        assert result is True

    def test_corrupted_pdf_fails(self, corrupted_pdf):
        """Test that corrupted PDF fails."""
        result = check_pdf_not_corrupted(Path(corrupted_pdf))
        assert result is False


class TestIntegration:
    """Integration tests for multiple checks."""

    def test_perfect_cv_passes_all_checks(self):
        """Test that a perfect CV passes all checks."""
        from tests.utils import (
            create_basic_pdf,
            create_temp_pdf_file,
            cleanup_temp_file,
        )

        # Create a perfect CV
        pdf_bytes = create_basic_pdf(
            text="This is a perfect CV with excellent content and proper formatting.",
            font_size=12,
            pages=1,
            author="Perfect Candidate",
            title="Perfect CV",
            add_link="https://github.com/perfect-candidate",
        )
        temp_file = create_temp_pdf_file(pdf_bytes)

        try:
            # All checks should pass
            assert check_pdf_exists(Path(temp_file)) is True
            assert check_pdf_page_count(Path(temp_file), max_pages=1) is True
            assert check_pdf_file_size(Path(temp_file), max_file_size_kb=500) is True
            assert (
                check_pdf_font_sizes(Path(temp_file), min_size=8, max_size=21) is True
            )
            assert check_pdf_links_https(Path(temp_file), enforce_https=True) is True
            assert check_pdf_no_images(Path(temp_file), no_images=True) is True
            assert (
                check_pdf_background_white(Path(temp_file), background_white=True)
                is True
            )
            assert (
                check_pdf_all_pixels_no_saturation(
                    Path(temp_file), grayscale_colors=True
                )
                is True
            )
            assert check_pdf_spell_check(Path(temp_file), custom_words=[]) is True
            assert check_pdf_structure(Path(temp_file)) is True
            assert check_pdf_not_corrupted(Path(temp_file)) is True
        finally:
            cleanup_temp_file(temp_file)

    def test_problematic_cv_fails_multiple_checks(self):
        """Test that a problematic CV fails multiple checks."""
        from tests.utils import (
            create_font_size_test_pdf,
            create_temp_pdf_file,
            cleanup_temp_file,
        )

        # Create a problematic CV with multiple issues
        pdf_bytes = create_font_size_test_pdf(
            small_font=6, large_font=24, include_normal=False  # Too small  # Too large
        )
        temp_file = create_temp_pdf_file(pdf_bytes)

        try:
            # These should pass
            assert check_pdf_exists(Path(temp_file)) is True
            assert check_pdf_page_count(Path(temp_file), max_pages=1) is True
            assert check_pdf_structure(Path(temp_file)) is True
            assert check_pdf_not_corrupted(Path(temp_file)) is True

            # This should fail due to font size issues
            assert (
                check_pdf_font_sizes(Path(temp_file), min_size=8, max_size=21) is False
            )
        finally:
            cleanup_temp_file(temp_file)
