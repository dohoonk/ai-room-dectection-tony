"""
Unit tests for image preprocessing module.
"""

import pytest
import numpy as np
import cv2
from src.image_preprocessor import (
    ImagePreprocessor,
    PreprocessingConfig,
    preprocess_image
)


@pytest.fixture
def sample_color_image():
    """Create a sample color image for testing."""
    # Create a 100x100 BGR image with some pattern
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[20:40, 20:80] = [255, 255, 255]  # White rectangle
    image[60:80, 20:80] = [0, 0, 0]  # Black rectangle
    return image


@pytest.fixture
def sample_grayscale_image():
    """Create a sample grayscale image for testing."""
    # Create a 100x100 grayscale image
    image = np.zeros((100, 100), dtype=np.uint8)
    image[20:40, 20:80] = 255  # White rectangle
    image[60:80, 20:80] = 0  # Black rectangle
    return image


class TestImagePreprocessor:
    """Test ImagePreprocessor class."""
    
    def test_initialization_default(self):
        """Test preprocessor initialization with default config."""
        preprocessor = ImagePreprocessor()
        assert preprocessor.config is not None
        assert preprocessor.config.gaussian_blur_kernel_size == 5
        assert preprocessor.config.use_histogram_equalization is True
    
    def test_initialization_custom_config(self):
        """Test preprocessor initialization with custom config."""
        config = PreprocessingConfig(
            gaussian_blur_kernel_size=7,
            use_histogram_equalization=False
        )
        preprocessor = ImagePreprocessor(config)
        assert preprocessor.config.gaussian_blur_kernel_size == 7
        assert preprocessor.config.use_histogram_equalization is False
    
    def test_to_grayscale_from_bgr(self, sample_color_image):
        """Test converting BGR image to grayscale."""
        preprocessor = ImagePreprocessor()
        gray = preprocessor.to_grayscale(sample_color_image)
        
        assert len(gray.shape) == 2, "Should be 2D grayscale"
        assert gray.shape[:2] == sample_color_image.shape[:2], "Should preserve dimensions"
        assert gray.dtype == np.uint8
    
    def test_to_grayscale_already_grayscale(self, sample_grayscale_image):
        """Test that grayscale image is returned as-is."""
        preprocessor = ImagePreprocessor()
        gray = preprocessor.to_grayscale(sample_grayscale_image)
        
        assert np.array_equal(gray, sample_grayscale_image), "Should return copy of grayscale"
        assert gray.shape == sample_grayscale_image.shape
    
    def test_to_grayscale_invalid_shape(self):
        """Test that invalid image shape raises error."""
        preprocessor = ImagePreprocessor()
        invalid_image = np.array([1, 2, 3])  # 1D array
        
        with pytest.raises(ValueError, match="Invalid image shape"):
            preprocessor.to_grayscale(invalid_image)
    
    def test_reduce_noise(self, sample_grayscale_image):
        """Test noise reduction with Gaussian blur."""
        preprocessor = ImagePreprocessor()
        denoised = preprocessor.reduce_noise(sample_grayscale_image)
        
        assert denoised.shape == sample_grayscale_image.shape
        assert denoised.dtype == np.uint8
    
    def test_reduce_noise_even_kernel_size(self):
        """Test that even kernel size is adjusted to odd."""
        config = PreprocessingConfig(gaussian_blur_kernel_size=6)
        preprocessor = ImagePreprocessor(config)
        image = np.zeros((100, 100), dtype=np.uint8)
        
        # Should not raise error (kernel size adjusted to 7)
        denoised = preprocessor.reduce_noise(image)
        assert denoised.shape == image.shape
    
    def test_enhance_contrast_histogram_equalization(self, sample_grayscale_image):
        """Test contrast enhancement with histogram equalization."""
        config = PreprocessingConfig(use_histogram_equalization=True)
        preprocessor = ImagePreprocessor(config)
        enhanced = preprocessor.enhance_contrast(sample_grayscale_image)
        
        assert enhanced.shape == sample_grayscale_image.shape
        assert enhanced.dtype == np.uint8
    
    def test_enhance_contrast_adaptive_equalization(self, sample_grayscale_image):
        """Test contrast enhancement with CLAHE."""
        config = PreprocessingConfig(
            use_histogram_equalization=False,
            use_adaptive_equalization=True
        )
        preprocessor = ImagePreprocessor(config)
        enhanced = preprocessor.enhance_contrast(sample_grayscale_image)
        
        assert enhanced.shape == sample_grayscale_image.shape
        assert enhanced.dtype == np.uint8
    
    def test_enhance_contrast_no_enhancement(self, sample_grayscale_image):
        """Test that image is unchanged when enhancement is disabled."""
        config = PreprocessingConfig(use_histogram_equalization=False)
        preprocessor = ImagePreprocessor(config)
        enhanced = preprocessor.enhance_contrast(sample_grayscale_image)
        
        assert np.array_equal(enhanced, sample_grayscale_image)
    
    def test_preprocess_full_pipeline(self, sample_color_image):
        """Test full preprocessing pipeline."""
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(sample_color_image)
        
        assert len(result.shape) == 2, "Should be grayscale"
        assert result.shape[:2] == sample_color_image.shape[:2]
        assert result.dtype == np.uint8
    
    def test_preprocess_grayscale_input(self, sample_grayscale_image):
        """Test preprocessing with grayscale input."""
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(sample_grayscale_image)
        
        assert len(result.shape) == 2, "Should remain grayscale"
        assert result.shape == sample_grayscale_image.shape
    
    def test_get_image_info_color(self, sample_color_image):
        """Test getting image information for color image."""
        preprocessor = ImagePreprocessor()
        info = preprocessor.get_image_info(sample_color_image)
        
        assert info['shape'] == sample_color_image.shape
        assert info['is_grayscale'] is False
        assert info['channels'] == 3
        assert 'min_value' in info
        assert 'max_value' in info
        assert 'mean_value' in info
    
    def test_get_image_info_grayscale(self, sample_grayscale_image):
        """Test getting image information for grayscale image."""
        preprocessor = ImagePreprocessor()
        info = preprocessor.get_image_info(sample_grayscale_image)
        
        assert info['shape'] == sample_grayscale_image.shape
        assert info['is_grayscale'] is True
        assert info['channels'] == 1


class TestConvenienceFunction:
    """Test convenience function preprocess_image."""
    
    def test_preprocess_image_default(self, sample_color_image):
        """Test convenience function with default config."""
        result = preprocess_image(sample_color_image)
        
        assert len(result.shape) == 2, "Should be grayscale"
        assert result.shape[:2] == sample_color_image.shape[:2]
    
    def test_preprocess_image_custom_config(self, sample_color_image):
        """Test convenience function with custom config."""
        config = PreprocessingConfig(use_histogram_equalization=False)
        result = preprocess_image(sample_color_image, config)
        
        assert len(result.shape) == 2, "Should be grayscale"
        assert result.shape[:2] == sample_color_image.shape[:2]

