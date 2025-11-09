"""
Unit tests for line detection module.
"""

import pytest
import numpy as np
import cv2
from src.line_detector import (
    LineDetector,
    EdgeDetectionConfig,
    LineDetectionConfig,
    LineDetectionParams,
    detect_lines_from_image
)


@pytest.fixture
def sample_image_with_lines():
    """Create a sample image with clear lines for testing."""
    # Create a 200x200 grayscale image with horizontal and vertical lines
    image = np.zeros((200, 200), dtype=np.uint8)
    
    # Horizontal line
    image[50, 20:180] = 255
    
    # Vertical line
    image[20:180, 100] = 255
    
    # Diagonal line
    for i in range(50, 150):
        x = i
        y = i
        if x < 200 and y < 200:
            image[y, x] = 255
    
    return image


@pytest.fixture
def sample_image_no_lines():
    """Create a sample image with no clear lines."""
    # Create a uniform grayscale image
    image = np.ones((100, 100), dtype=np.uint8) * 128
    return image


class TestEdgeDetectionConfig:
    """Test EdgeDetectionConfig dataclass."""
    
    def test_default_config(self):
        """Test default edge detection configuration."""
        config = EdgeDetectionConfig()
        assert config.low_threshold == 50
        assert config.high_threshold == 150
        assert config.aperture_size == 3
        assert config.l2_gradient is False
    
    def test_custom_config(self):
        """Test custom edge detection configuration."""
        config = EdgeDetectionConfig(
            low_threshold=100,
            high_threshold=200,
            aperture_size=5,
            l2_gradient=True
        )
        assert config.low_threshold == 100
        assert config.high_threshold == 200
        assert config.aperture_size == 5
        assert config.l2_gradient is True


class TestLineDetectionConfig:
    """Test LineDetectionConfig dataclass."""
    
    def test_default_config(self):
        """Test default line detection configuration."""
        config = LineDetectionConfig()
        assert config.rho == 1.0
        assert config.theta == np.pi / 180
        assert config.threshold == 100
        assert config.min_line_length == 50.0
        assert config.max_line_gap == 10.0
    
    def test_custom_config(self):
        """Test custom line detection configuration."""
        config = LineDetectionConfig(
            rho=2.0,
            threshold=50,
            min_line_length=30.0,
            max_line_gap=5.0
        )
        assert config.rho == 2.0
        assert config.threshold == 50
        assert config.min_line_length == 30.0
        assert config.max_line_gap == 5.0


class TestLineDetectionParams:
    """Test LineDetectionParams dataclass."""
    
    def test_default_params(self):
        """Test default parameters initialization."""
        params = LineDetectionParams()
        assert params.edge_config is not None
        assert params.line_config is not None
        assert isinstance(params.edge_config, EdgeDetectionConfig)
        assert isinstance(params.line_config, LineDetectionConfig)
    
    def test_custom_params(self):
        """Test custom parameters initialization."""
        edge_config = EdgeDetectionConfig(low_threshold=100)
        line_config = LineDetectionConfig(threshold=50)
        params = LineDetectionParams(
            edge_config=edge_config,
            line_config=line_config
        )
        assert params.edge_config.low_threshold == 100
        assert params.line_config.threshold == 50


class TestLineDetector:
    """Test LineDetector class."""
    
    def test_initialization_default(self):
        """Test detector initialization with default params."""
        detector = LineDetector()
        assert detector.params is not None
        assert detector.params.edge_config is not None
        assert detector.params.line_config is not None
    
    def test_initialization_custom_params(self):
        """Test detector initialization with custom params."""
        params = LineDetectionParams()
        params.edge_config.low_threshold = 100
        detector = LineDetector(params)
        assert detector.params.edge_config.low_threshold == 100
    
    def test_detect_edges(self, sample_image_with_lines):
        """Test edge detection."""
        detector = LineDetector()
        edges = detector.detect_edges(sample_image_with_lines)
        
        assert edges.shape == sample_image_with_lines.shape
        assert edges.dtype == np.uint8
        # Edges should be binary (0 or 255)
        assert np.all((edges == 0) | (edges == 255))
    
    def test_detect_edges_invalid_aperture(self):
        """Test that invalid aperture size is adjusted."""
        config = EdgeDetectionConfig(aperture_size=4)  # Invalid, should be 3, 5, or 7
        params = LineDetectionParams(edge_config=config)
        detector = LineDetector(params)
        
        image = np.zeros((100, 100), dtype=np.uint8)
        image[50, 20:80] = 255  # Horizontal line
        
        # Should not raise error (aperture adjusted)
        edges = detector.detect_edges(image)
        assert edges.shape == image.shape
    
    def test_detect_lines(self, sample_image_with_lines):
        """Test line detection from edges."""
        detector = LineDetector()
        edges = detector.detect_edges(sample_image_with_lines)
        lines = detector.detect_lines(edges)
        
        assert isinstance(lines, list)
        # Should detect at least some lines
        assert len(lines) > 0
        
        # Verify line format
        for line in lines:
            assert len(line) == 4, "Line should be (x1, y1, x2, y2)"
            x1, y1, x2, y2 = line
            assert isinstance(x1, (int, float))
            assert isinstance(y1, (int, float))
            assert isinstance(x2, (int, float))
            assert isinstance(y2, (int, float))
    
    def test_detect_lines_no_edges(self):
        """Test line detection with no edges."""
        detector = LineDetector()
        edges = np.zeros((100, 100), dtype=np.uint8)
        lines = detector.detect_lines(edges)
        
        assert isinstance(lines, list)
        assert len(lines) == 0
    
    def test_detect_lines_from_image(self, sample_image_with_lines):
        """Test complete pipeline: edges then lines."""
        detector = LineDetector()
        lines = detector.detect_lines_from_image(sample_image_with_lines)
        
        assert isinstance(lines, list)
        # Should detect lines from the test image
        assert len(lines) > 0
    
    def test_detect_lines_from_image_no_lines(self, sample_image_no_lines):
        """Test line detection on image with no clear lines."""
        detector = LineDetector()
        lines = detector.detect_lines_from_image(sample_image_no_lines)
        
        assert isinstance(lines, list)
        # May or may not detect lines depending on noise
    
    def test_get_edge_statistics(self, sample_image_with_lines):
        """Test edge statistics calculation."""
        detector = LineDetector()
        edges = detector.detect_edges(sample_image_with_lines)
        stats = detector.get_edge_statistics(edges)
        
        assert 'edge_pixel_count' in stats
        assert 'total_pixels' in stats
        assert 'edge_density' in stats
        assert 'image_shape' in stats
        assert stats['total_pixels'] == edges.shape[0] * edges.shape[1]
        assert 0.0 <= stats['edge_density'] <= 1.0
    
    def test_get_line_statistics(self):
        """Test line statistics calculation."""
        detector = LineDetector()
        
        # Test with empty lines
        stats = detector.get_line_statistics([])
        assert stats['line_count'] == 0
        assert stats['total_length'] == 0.0
        
        # Test with lines
        lines = [
            (0.0, 0.0, 100.0, 0.0),  # Horizontal line, length 100
            (0.0, 0.0, 0.0, 50.0),   # Vertical line, length 50
        ]
        stats = detector.get_line_statistics(lines)
        assert stats['line_count'] == 2
        assert stats['total_length'] == 150.0
        assert stats['avg_length'] == 75.0
        assert stats['min_length'] == 50.0
        assert stats['max_length'] == 100.0


class TestConvenienceFunction:
    """Test convenience function detect_lines_from_image."""
    
    def test_detect_lines_default(self, sample_image_with_lines):
        """Test convenience function with default params."""
        lines = detect_lines_from_image(sample_image_with_lines)
        
        assert isinstance(lines, list)
        # Should detect lines from the test image
        assert len(lines) > 0
    
    def test_detect_lines_custom_params(self, sample_image_with_lines):
        """Test convenience function with custom params."""
        params = LineDetectionParams()
        params.line_config.min_line_length = 100.0  # Higher threshold
        lines = detect_lines_from_image(sample_image_with_lines, params)
        
        assert isinstance(lines, list)
        # May detect fewer lines with higher threshold

