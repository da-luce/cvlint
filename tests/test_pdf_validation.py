"""Comprehensive tests for PDF validation checks."""

import pytest
from pathlib import Path
from src.cvlint.main import (
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
    check_pdf_not_corrupted
)


class TestPdfExists:
    """Test PDF file existence validation."""
    
    def test_pdf_exists_valid_file(self, valid_pdf, mock_pdf_path):
        """Test that check passes when PDF file exists."""
        with mock_pdf_path(valid_pdf):
            # Should not raise an exception
            check_pdf_exists()
    
    def test_pdf_exists_missing_file(self, mock_pdf_path):
        """Test that check fails when PDF file doesn't exist."""
        with mock_pdf_path("/nonexistent/file.pdf"):
            with pytest.raises(AssertionError, match="CV PDF not found"):
                check_pdf_exists()


class TestPdfPageCount:
    """Test PDF page count validation."""
    
    def test_single_page_pdf_passes(self, valid_pdf, mock_pdf_path):
        """Test that single-page PDF passes."""
        with mock_pdf_path(valid_pdf):
            # Should not raise an exception
            check_pdf_page_count()
    
    def test_multi_page_pdf_fails(self, multi_page_pdf, mock_pdf_path):
        """Test that multi-page PDF fails."""
        with mock_pdf_path(multi_page_pdf):
            with pytest.raises(AssertionError, match="CV is 3 pages"):
                check_pdf_page_count()


class TestPdfFileSize:
    """Test PDF file size validation."""
    
    def test_normal_size_pdf_passes(self, valid_pdf, mock_pdf_path):
        """Test that normal-sized PDF passes."""
        with mock_pdf_path(valid_pdf):
            # Should not raise an exception
            check_pdf_file_size()
    
    def test_large_pdf_fails(self, large_pdf, mock_pdf_path, mock_config):
        """Test that oversized PDF fails."""
        with mock_pdf_path(large_pdf):
            with mock_config(MAX_FILE_SIZE_KB=50):  # Set limit to 50KB so 60KB PDF fails
                with pytest.raises(AssertionError, match="CV file size is"):
                    check_pdf_file_size()


class TestPdfFontSizes:
    """Test PDF font size validation."""
    
    def test_normal_fonts_pass(self, valid_pdf, mock_pdf_path):
        """Test that normal font sizes pass."""
        with mock_pdf_path(valid_pdf):
            # Should not raise an exception
            check_pdf_font_sizes()
    
    def test_small_fonts_fail(self, small_font_pdf, mock_pdf_path):
        """Test that fonts below minimum size fail."""
        with mock_pdf_path(small_font_pdf):
            with pytest.raises(AssertionError, match="smaller than minimum"):
                check_pdf_font_sizes()
    
    def test_large_fonts_fail(self, large_font_pdf, mock_pdf_path):
        """Test that fonts above maximum size fail."""
        with mock_pdf_path(large_font_pdf):
            with pytest.raises(AssertionError, match="larger than maximum"):
                check_pdf_font_sizes()
    
    def test_custom_font_size_limits(self, valid_pdf, mock_pdf_path):
        """Test custom font size limits."""
        with mock_pdf_path(valid_pdf):
            # Should pass with custom limits that include the font size
            check_pdf_font_sizes(min_size=10, max_size=15)


class TestPdfLinksHttps:
    """Test PDF HTTPS links validation."""
    
    def test_https_links_pass(self, https_link_pdf, mock_pdf_path, mock_config):
        """Test that HTTPS links pass when enforcement is enabled."""
        with mock_pdf_path(https_link_pdf):
            with mock_config(ENFORCE_HTTPS=True):
                # Should not raise an exception
                check_pdf_links_https()
    
    def test_http_links_fail(self, http_link_pdf, mock_pdf_path, mock_config):
        """Test that HTTP links fail when enforcement is enabled."""
        with mock_pdf_path(http_link_pdf):
            with mock_config(ENFORCE_HTTPS=True):
                with pytest.raises(AssertionError, match="does not use HTTPS"):
                    check_pdf_links_https()
    
    def test_https_enforcement_disabled(self, http_link_pdf, mock_pdf_path, mock_config):
        """Test that check is skipped when HTTPS enforcement is disabled."""
        with mock_pdf_path(http_link_pdf):
            with mock_config(ENFORCE_HTTPS=False):
                with pytest.raises(pytest.skip.Exception):
                    check_pdf_links_https()
    
    def test_no_links_pass(self, valid_pdf, mock_pdf_path, mock_config):
        """Test that PDFs without links pass."""
        with mock_pdf_path(valid_pdf):
            with mock_config(ENFORCE_HTTPS=True):
                # Should not raise an exception
                check_pdf_links_https()


class TestPdfNoImages:
    """Test PDF image validation."""
    
    def test_no_images_pass(self, valid_pdf, mock_pdf_path, mock_config):
        """Test that PDFs without images pass."""
        with mock_pdf_path(valid_pdf):
            with mock_config(NO_IMAGES=True):
                # Should not raise an exception
                check_pdf_no_images()
    
    def test_with_images_fail(self, pdf_with_image, mock_pdf_path, mock_config):
        """Test that PDFs with images fail when NO_IMAGES is True."""
        with mock_pdf_path(pdf_with_image):
            with mock_config(NO_IMAGES=True):
                with pytest.raises(AssertionError, match="Found image"):
                    check_pdf_no_images()
    
    def test_image_checking_disabled(self, pdf_with_image, mock_pdf_path, mock_config):
        """Test that check is skipped when image checking is disabled."""
        with mock_pdf_path(pdf_with_image):
            with mock_config(NO_IMAGES=False):
                with pytest.raises(pytest.skip.Exception):
                    check_pdf_no_images()


class TestPdfBackgroundWhite:
    """Test PDF background color validation."""
    
    def test_white_background_passes(self, valid_pdf, mock_pdf_path, mock_config):
        """Test that white background passes."""
        with mock_pdf_path(valid_pdf):
            with mock_config(BACKGROUND_WHITE=True):
                # Should not raise an exception
                check_pdf_background_white()
    
    def test_colored_background_fails(self, colored_background_pdf, mock_pdf_path, mock_config):
        """Test that colored background fails."""
        with mock_pdf_path(colored_background_pdf):
            with mock_config(BACKGROUND_WHITE=True):
                with pytest.raises(AssertionError, match="Expected white background"):
                    check_pdf_background_white()
    
    def test_background_checking_disabled(self, colored_background_pdf, mock_pdf_path, mock_config):
        """Test that check is skipped when background checking is disabled."""
        with mock_pdf_path(colored_background_pdf):
            with mock_config(BACKGROUND_WHITE=False):
                with pytest.raises(pytest.skip.Exception):
                    check_pdf_background_white()


class TestPdfGrayscaleColors:
    """Test PDF grayscale color validation."""
    
    def test_grayscale_colors_pass(self, grayscale_pdf, mock_pdf_path, mock_config):
        """Test that grayscale colors pass."""
        with mock_pdf_path(grayscale_pdf):
            with mock_config(GRAYSCALE_COLORS=True):
                # Should not raise an exception
                check_pdf_all_pixels_no_saturation()
    
    def test_saturated_colors_fail(self, saturated_colors_pdf, mock_pdf_path, mock_config):
        """Test that saturated colors fail."""
        with mock_pdf_path(saturated_colors_pdf):
            with mock_config(GRAYSCALE_COLORS=True):
                with pytest.raises(AssertionError, match="Pixel with saturation"):
                    check_pdf_all_pixels_no_saturation()
    
    def test_grayscale_checking_disabled(self, saturated_colors_pdf, mock_pdf_path, mock_config):
        """Test that check is skipped when grayscale checking is disabled."""
        with mock_pdf_path(saturated_colors_pdf):
            with mock_config(GRAYSCALE_COLORS=False):
                with pytest.raises(pytest.skip.Exception):
                    check_pdf_all_pixels_no_saturation()
    
    def test_custom_tolerance(self, saturated_colors_pdf, mock_pdf_path, mock_config):
        """Test custom saturation tolerance."""
        with mock_pdf_path(saturated_colors_pdf):
            with mock_config(GRAYSCALE_COLORS=True):
                # Should still fail even with higher tolerance for very saturated colors
                with pytest.raises(AssertionError):
                    check_pdf_all_pixels_no_saturation(tolerance=0.1)


class TestPdfSpellCheck:
    """Test PDF spell checking validation."""
    
    def test_correct_spelling_passes(self, valid_pdf, mock_pdf_path, mock_config):
        """Test that correctly spelled text passes."""
        with mock_pdf_path(valid_pdf):
            with mock_config(CUSTOM_WORDS=[]):
                # Should not raise an exception
                check_pdf_spell_check()
    
    def test_spelling_errors_fail(self, spelling_errors_pdf, mock_pdf_path, mock_config):
        """Test that spelling errors fail."""
        with mock_pdf_path(spelling_errors_pdf):
            with mock_config(CUSTOM_WORDS=[]):
                with pytest.raises(AssertionError, match="Misspelled words"):
                    check_pdf_spell_check()
    
    def test_custom_words_allowed(self, mock_pdf_path, mock_config):
        """Test that custom words are allowed."""
        from tests.utils import create_basic_pdf, create_temp_pdf_file, cleanup_temp_file
        
        # Create PDF with technical terms
        pdf_bytes = create_basic_pdf(
            text="I have experience with JavaScript and PostgreSQL databases.",
            author="Test Author",
            title="Technical CV"
        )
        temp_file = create_temp_pdf_file(pdf_bytes)
        
        try:
            with mock_pdf_path(temp_file):
                with mock_config(CUSTOM_WORDS=["javascript", "postgresql"]):
                    # Should not raise an exception
                    check_pdf_spell_check()
        finally:
            cleanup_temp_file(temp_file)
    
    def test_capitalization_rules(self, mock_pdf_path, mock_config):
        """Test capitalization rules for custom words."""
        from tests.utils import create_basic_pdf, create_temp_pdf_file, cleanup_temp_file
        
        # Create PDF with incorrectly capitalized technical terms (using a made-up framework name)
        pdf_bytes = create_basic_pdf(
            text="I have experience with reactjs and REACTJS framework development.",
            author="Test Author",
            title="Capitalization Test CV"
        )
        temp_file = create_temp_pdf_file(pdf_bytes)
        
        try:
            with mock_pdf_path(temp_file):
                with mock_config(CUSTOM_WORDS=["ReactJS"]):  # Specific capitalization required
                    with pytest.raises(AssertionError, match="Capitalization errors"):
                        check_pdf_spell_check()
        finally:
            cleanup_temp_file(temp_file)


class TestPdfStructure:
    """Test PDF structure and metadata validation."""
    
    def test_valid_metadata_passes(self, valid_pdf, mock_pdf_path):
        """Test that valid metadata passes."""
        with mock_pdf_path(valid_pdf):
            # Should not raise an exception
            check_pdf_structure()
    
    def test_missing_metadata_fails(self, no_metadata_pdf, mock_pdf_path):
        """Test that missing metadata fails."""
        with mock_pdf_path(no_metadata_pdf):
            with pytest.raises(AssertionError, match="PDF should have a valid Author"):
                check_pdf_structure()
    
    def test_empty_metadata_fails(self, mock_pdf_path):
        """Test that empty metadata fails."""
        from tests.utils import create_basic_pdf, create_temp_pdf_file, cleanup_temp_file
        
        # Create PDF with empty metadata
        pdf_bytes = create_basic_pdf(
            text="CV with empty metadata",
            author="",  # Empty author
            title=""    # Empty title
        )
        temp_file = create_temp_pdf_file(pdf_bytes)
        
        try:
            with mock_pdf_path(temp_file):
                with pytest.raises(AssertionError, match="PDF should have a valid Author"):
                    check_pdf_structure()
        finally:
            cleanup_temp_file(temp_file)


class TestPdfNotCorrupted:
    """Test PDF corruption validation."""
    
    def test_valid_pdf_passes(self, valid_pdf, mock_pdf_path):
        """Test that valid PDF passes corruption check."""
        with mock_pdf_path(valid_pdf):
            # Should not raise an exception
            check_pdf_not_corrupted()
    
    def test_corrupted_pdf_fails(self, corrupted_pdf, mock_pdf_path):
        """Test that corrupted PDF fails."""
        with mock_pdf_path(corrupted_pdf):
            with pytest.raises(AssertionError, match="PDF appears to be corrupted"):
                check_pdf_not_corrupted()


class TestIntegration:
    """Integration tests for multiple checks."""
    
    def test_perfect_cv_passes_all_checks(self, mock_pdf_path, mock_config):
        """Test that a perfect CV passes all checks."""
        from tests.utils import create_basic_pdf, create_temp_pdf_file, cleanup_temp_file
        
        # Create a perfect CV
        pdf_bytes = create_basic_pdf(
            text="This is a perfect CV with excellent content and proper formatting.",
            font_size=12,
            pages=1,
            author="Perfect Candidate",
            title="Perfect CV",
            add_link="https://github.com/perfect-candidate"
        )
        temp_file = create_temp_pdf_file(pdf_bytes)
        
        try:
            with mock_pdf_path(temp_file):
                with mock_config(
                    ENFORCE_HTTPS=True,
                    NO_IMAGES=True,
                    BACKGROUND_WHITE=True,
                    GRAYSCALE_COLORS=True,
                    CUSTOM_WORDS=[]
                ):
                    # All checks should pass
                    check_pdf_exists()
                    check_pdf_page_count()
                    check_pdf_file_size()
                    check_pdf_font_sizes()
                    check_pdf_links_https()
                    check_pdf_no_images()
                    check_pdf_background_white()
                    check_pdf_all_pixels_no_saturation()
                    check_pdf_spell_check()
                    check_pdf_structure()
                    check_pdf_not_corrupted()
        finally:
            cleanup_temp_file(temp_file)
    
    def test_problematic_cv_fails_multiple_checks(self, mock_pdf_path, mock_config):
        """Test that a problematic CV fails multiple checks."""
        from tests.utils import create_font_size_test_pdf, create_temp_pdf_file, cleanup_temp_file
        
        # Create a problematic CV with multiple issues
        pdf_bytes = create_font_size_test_pdf(
            small_font=6,   # Too small
            large_font=24,  # Too large
            include_normal=False
        )
        temp_file = create_temp_pdf_file(pdf_bytes)
        
        try:
            with mock_pdf_path(temp_file):
                with mock_config(
                    ENFORCE_HTTPS=True,
                    NO_IMAGES=True,
                    BACKGROUND_WHITE=True,
                    GRAYSCALE_COLORS=True,
                    CUSTOM_WORDS=[]
                ):
                    # These should pass
                    check_pdf_exists()
                    check_pdf_page_count()
                    check_pdf_structure()
                    check_pdf_not_corrupted()
                    
                    # This should fail
                    with pytest.raises(AssertionError):
                        check_pdf_font_sizes()
        finally:
            cleanup_temp_file(temp_file)
