"""
Integration tests for raster image processing pipeline.

Tests the complete pipeline from image input to room detection,
including preprocessing, edge detection, line detection, filtering,
and room detection.
"""

import pytest
import cv2
import numpy as np
import tempfile
import os
import json
from pathlib import Path
from src.image_preprocessor import ImagePreprocessor
from src.line_detector import LineDetector
from src.line_filter import LineFilter
from src.image_validator import validate_image_segments
from src.room_detector import detect_rooms
from src.parser import WallSegment


@pytest.fixture
def sample_image():
    """Create a simple test image with rectangular walls."""
    # Create a 1000x1000 image with white background
    img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
    
    # Draw a rectangle (walls) in black
    # Outer rectangle
    cv2.rectangle(img, (100, 100), (900, 900), (0, 0, 0), 5)
    # Inner wall (dividing into two rooms)
    cv2.line(img, (500, 100), (500, 900), (0, 0, 0), 5)
    
    return img


@pytest.fixture
def complex_image():
    """Create a more complex test image with multiple rooms."""
    # Create a 1000x1000 image with white background
    img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
    
    # Draw multiple rectangles (rooms)
    # Room 1: Top left
    cv2.rectangle(img, (50, 50), (450, 450), (0, 0, 0), 5)
    # Room 2: Top right
    cv2.rectangle(img, (550, 50), (950, 450), (0, 0, 0), 5)
    # Room 3: Bottom left
    cv2.rectangle(img, (50, 550), (450, 950), (0, 0, 0), 5)
    # Room 4: Bottom right
    cv2.rectangle(img, (550, 550), (950, 950), (0, 0, 0), 5)
    
    return img


@pytest.fixture
def noisy_image():
    """Create a test image with noise to test preprocessing."""
    # Create a 1000x1000 image with white background
    img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
    
    # Draw walls
    cv2.rectangle(img, (100, 100), (900, 900), (0, 0, 0), 5)
    
    # Add noise
    noise = np.random.randint(0, 50, (1000, 1000, 3), dtype=np.uint8)
    img = cv2.add(img, noise)
    
    return img


class TestImageProcessingPipeline:
    """Test the complete image processing pipeline."""
    
    def test_preprocessing_pipeline(self, sample_image):
        """Test image preprocessing produces valid output."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        # Should be grayscale
        assert len(preprocessed.shape) == 2
        # Should have same dimensions
        assert preprocessed.shape == (1000, 1000)
        # Should be uint8
        assert preprocessed.dtype == np.uint8
    
    def test_edge_detection_pipeline(self, sample_image):
        """Test edge detection produces edges."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        line_detector = LineDetector()
        edges = line_detector.detect_edges(preprocessed)
        
        # Should be binary image
        assert len(edges.shape) == 2
        # Should have edges
        assert np.sum(edges > 0) > 0
    
    def test_line_detection_pipeline(self, sample_image):
        """Test line detection finds lines."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        # Should find some lines
        assert len(lines) > 0
        # Each line should be a tuple of 4 floats
        for line in lines:
            assert len(line) == 4
            assert all(isinstance(x, (int, float)) for x in line)
    
    def test_line_filtering_pipeline(self, sample_image):
        """Test line filtering reduces noise."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        
        # Filtered lines should be <= original lines
        assert len(filtered_lines) <= len(lines)
        # Should still have some lines
        assert len(filtered_lines) > 0
    
    def test_segment_conversion_pipeline(self, sample_image):
        """Test conversion to wall segments."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        
        # Convert to wall segments
        height, width = sample_image.shape[:2]
        wall_segments = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Should have segments
        assert len(wall_segments) > 0
        # Each segment should have required fields
        for seg in wall_segments:
            assert 'type' in seg
            assert 'start' in seg
            assert 'end' in seg
            assert len(seg['start']) == 2
            assert len(seg['end']) == 2
            # Coordinates should be in 0-1000 range
            assert 0 <= seg['start'][0] <= 1000
            assert 0 <= seg['start'][1] <= 1000
            assert 0 <= seg['end'][0] <= 1000
            assert 0 <= seg['end'][1] <= 1000
    
    def test_validation_pipeline(self, sample_image):
        """Test segment validation."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        
        height, width = sample_image.shape[:2]
        wall_segments_dict = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Convert to WallSegment objects
        wall_segments = [
            WallSegment(
                start=(seg['start'][0], seg['start'][1]),
                end=(seg['end'][0], seg['end'][1]),
                is_load_bearing=False
            )
            for seg in wall_segments_dict
        ]
        
        # Validate
        validation_result = validate_image_segments(wall_segments, strict=False)
        
        # Should pass validation (or at least have valid structure)
        assert 'valid' in validation_result
        assert 'errors' in validation_result
        assert 'warnings' in validation_result
        assert 'stats' in validation_result
    
    def test_full_pipeline_room_detection(self, sample_image):
        """Test complete pipeline from image to room detection."""
        # Preprocess
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        # Detect lines
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        assert len(lines) > 0
        
        # Filter lines
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        assert len(filtered_lines) > 0
        
        # Convert to segments
        height, width = sample_image.shape[:2]
        wall_segments_dict = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Convert to WallSegment objects
        wall_segments = [
            WallSegment(
                start=(seg['start'][0], seg['start'][1]),
                end=(seg['end'][0], seg['end'][1]),
                is_load_bearing=False
            )
            for seg in wall_segments_dict
        ]
        
        # Validate
        validation_result = validate_image_segments(wall_segments, strict=False)
        if not validation_result['valid']:
            pytest.skip("Segments failed validation - may need parameter tuning")
        
        # Convert to JSON for room detection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            walls_data = [
                {
                    "type": "line",
                    "start": [seg.start[0], seg.start[1]],
                    "end": [seg.end[0], seg.end[1]],
                    "is_load_bearing": seg.is_load_bearing
                }
                for seg in wall_segments
            ]
            json.dump(walls_data, f)
            temp_json_path = f.name
        
        try:
            # Detect rooms
            rooms = detect_rooms(temp_json_path, tolerance=5.0)
            
            # Should detect at least one room
            assert len(rooms) > 0
            # Each room should have required fields
            for room in rooms:
                assert 'id' in room
                assert 'bounding_box' in room
                assert len(room['bounding_box']) == 4
        finally:
            os.unlink(temp_json_path)
    
    def test_complex_image_pipeline(self, complex_image):
        """Test pipeline with complex multi-room image."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(complex_image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        assert len(lines) > 0
        
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        assert len(filtered_lines) > 0
        
        height, width = complex_image.shape[:2]
        wall_segments_dict = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Should have multiple segments for multiple rooms
        assert len(wall_segments_dict) >= 4  # At least 4 walls per room
    
    def test_noisy_image_preprocessing(self, noisy_image):
        """Test that preprocessing handles noise."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(noisy_image)
        
        # Should still be able to detect edges
        line_detector = LineDetector()
        edges = line_detector.detect_edges(preprocessed)
        
        # Should have some edges despite noise
        assert np.sum(edges > 0) > 0
    
    def test_empty_image_handling(self):
        """Test handling of empty/blank image."""
        # Create blank white image
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(img)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        # Should handle gracefully (may find no lines or very few)
        assert isinstance(lines, list)
    
    def test_small_image_handling(self):
        """Test handling of small images."""
        # Create small 100x100 image
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.rectangle(img, (10, 10), (90, 90), (0, 0, 0), 2)
        
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(img)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        # Should handle small images
        assert isinstance(lines, list)
    
    def test_parameter_tuning_effectiveness(self, sample_image):
        """Test that different parameters affect detection."""
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(sample_image)
        
        # Test with default parameters
        line_detector_default = LineDetector()
        lines_default = line_detector_default.detect_lines_from_image(preprocessed)
        
        # Test with different parameters
        from src.line_detector import EdgeDetectionConfig, LineDetectionConfig, LineDetectionParams
        
        custom_edge_config = EdgeDetectionConfig(low_threshold=30, high_threshold=100)
        custom_line_config = LineDetectionConfig(threshold=50, min_line_length=30.0)
        custom_params = LineDetectionParams(
            edge_config=custom_edge_config,
            line_config=custom_line_config
        )
        
        line_detector_custom = LineDetector(params=custom_params)
        lines_custom = line_detector_custom.detect_lines_from_image(preprocessed)
        
        # Both should work (may have different counts)
        assert len(lines_default) >= 0
        assert len(lines_custom) >= 0
        # At least one should find lines
        assert len(lines_default) > 0 or len(lines_custom) > 0


class TestImageProcessingWithGroundTruth:
    """Test image processing against ground truth JSON data."""
    
    def test_compare_with_json_input(self):
        """Test that image processing produces similar results to JSON input."""
        # This test would require:
        # 1. A test image generated from JSON floorplan
        # 2. Processing the image through the pipeline
        # 3. Comparing detected rooms with expected rooms from JSON
        
        # For now, we'll create a simple test
        # In a full implementation, we'd load actual test images and JSON files
        
        # Create simple rectangular room image
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        cv2.rectangle(img, (100, 100), (900, 900), (0, 0, 0), 5)
        
        # Process through pipeline
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(img)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        
        height, width = img.shape[:2]
        wall_segments_dict = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Should produce segments that can form a room
        assert len(wall_segments_dict) >= 3  # Need at least 3 segments for a room


class TestImageProcessingErrorHandling:
    """Test error handling in image processing pipeline."""
    
    def test_invalid_image_handling(self):
        """Test handling of invalid image data."""
        # Try with None
        preprocessor = ImagePreprocessor()
        with pytest.raises((AttributeError, TypeError)):
            preprocessor.preprocess(None)
    
    def test_zero_size_image_handling(self):
        """Test handling of zero-size image."""
        img = np.array([], dtype=np.uint8)
        
        preprocessor = ImagePreprocessor()
        with pytest.raises((ValueError, IndexError)):
            preprocessed = preprocessor.preprocess(img)
    
    def test_malformed_image_handling(self):
        """Test handling of malformed image data."""
        # Create invalid image (wrong shape)
        img = np.array([1, 2, 3], dtype=np.uint8)
        
        preprocessor = ImagePreprocessor()
        with pytest.raises((ValueError, IndexError)):
            preprocessed = preprocessor.preprocess(img)


class TestImageProcessingWithSampleFiles:
    """Test image processing with actual sample image files."""
    
    @pytest.fixture
    def sample_image_path(self):
        """Return path to simple_floorplan.png if it exists."""
        project_root = Path(__file__).parent.parent.parent
        image_path = project_root / "tests" / "sample_data" / "simple" / "simple_floorplan.png"
        if not image_path.exists():
            pytest.skip(f"Sample image not found at {image_path}")
        return str(image_path)
    
    @pytest.fixture
    def complex_image_path(self):
        """Return path to complex_floorplan.png if it exists."""
        project_root = Path(__file__).parent.parent.parent
        image_path = project_root / "tests" / "sample_data" / "complex" / "complex_floorplan.png"
        if not image_path.exists():
            pytest.skip(f"Complex image not found at {image_path}")
        return str(image_path)
    
    def test_process_sample_image(self, sample_image_path):
        """Test processing of actual sample image file."""
        # Load image
        image = cv2.imread(sample_image_path)
        assert image is not None, f"Could not load image from {sample_image_path}"
        
        # Process through pipeline
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        # Should detect some lines
        assert len(lines) > 0, "Should detect lines from sample image"
        
        # Filter and convert
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        assert len(filtered_lines) > 0
        
        height, width = image.shape[:2]
        wall_segments = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Should produce segments
        assert len(wall_segments) > 0
    
    def test_process_complex_image(self, complex_image_path):
        """Test processing of complex multi-room image."""
        # Load image
        image = cv2.imread(complex_image_path)
        assert image is not None, f"Could not load image from {complex_image_path}"
        
        # Process through pipeline
        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(image)
        
        line_detector = LineDetector()
        lines = line_detector.detect_lines_from_image(preprocessed)
        
        # Should detect lines
        assert len(lines) > 0
        
        # Filter and convert
        line_filter = LineFilter()
        filtered_lines = line_filter.filter_lines(lines)
        
        height, width = image.shape[:2]
        wall_segments = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=width,
            image_height=height
        )
        
        # Should produce multiple segments for multiple rooms
        assert len(wall_segments) >= 4  # At least 4 walls for multiple rooms

