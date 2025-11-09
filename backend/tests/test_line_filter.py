"""
Unit tests for line filtering and segment conversion module.
"""

import pytest
import math
from src.line_filter import (
    LineFilter,
    LineFilterConfig,
    filter_and_convert_lines
)


@pytest.fixture
def sample_lines():
    """Create sample lines for testing."""
    return [
        (0.0, 0.0, 100.0, 0.0),      # Horizontal line, length 100
        (0.0, 0.0, 0.0, 50.0),      # Vertical line, length 50
        (10.0, 10.0, 110.0, 10.0),  # Horizontal line, length 100 (parallel to first)
        (5.0, 0.0, 105.0, 0.0),     # Horizontal line, length 100 (duplicate of first)
        (0.0, 0.0, 5.0, 0.0),       # Short horizontal line, length 5
        (0.0, 0.0, 0.0, 20000.0),   # Very long vertical line
    ]


@pytest.fixture
def sample_angled_lines():
    """Create sample lines with various angles."""
    return [
        (0.0, 0.0, 100.0, 0.0),      # Horizontal (0 degrees)
        (0.0, 0.0, 0.0, 100.0),      # Vertical (90 degrees)
        (0.0, 0.0, 100.0, 10.0),     # Slight angle (~5.7 degrees)
        (0.0, 0.0, 100.0, 50.0),     # Steep angle (~26.6 degrees)
    ]


class TestLineFilterConfig:
    """Test LineFilterConfig dataclass."""
    
    def test_default_config(self):
        """Test default filtering configuration."""
        config = LineFilterConfig()
        assert config.min_length == 20.0
        assert config.max_length == 10000.0
        assert config.prefer_horizontal_vertical is True
        assert config.angle_tolerance == 5.0
        assert config.group_parallel_threshold == 2.0
        assert config.remove_duplicates is True
    
    def test_custom_config(self):
        """Test custom filtering configuration."""
        config = LineFilterConfig(
            min_length=50.0,
            prefer_horizontal_vertical=False,
            angle_tolerance=10.0
        )
        assert config.min_length == 50.0
        assert config.prefer_horizontal_vertical is False
        assert config.angle_tolerance == 10.0


class TestLineFilter:
    """Test LineFilter class."""
    
    def test_initialization_default(self):
        """Test filter initialization with default config."""
        filter_obj = LineFilter()
        assert filter_obj.config is not None
        assert filter_obj.config.min_length == 20.0
    
    def test_initialization_custom_config(self):
        """Test filter initialization with custom config."""
        config = LineFilterConfig(min_length=50.0)
        filter_obj = LineFilter(config)
        assert filter_obj.config.min_length == 50.0
    
    def test_filter_by_length(self, sample_lines):
        """Test filtering lines by length."""
        config = LineFilterConfig(min_length=20.0, max_length=1000.0)
        filter_obj = LineFilter(config)
        filtered = filter_obj.filter_by_length(sample_lines)
        
        # Should filter out:
        # - Line 4: length 5 (< 20)
        # - Line 5: length 20000 (> 1000)
        assert len(filtered) == 4
        assert (0.0, 0.0, 100.0, 0.0) in filtered
        assert (0.0, 0.0, 0.0, 50.0) in filtered
    
    def test_filter_by_length_empty(self):
        """Test filtering with no lines."""
        filter_obj = LineFilter()
        filtered = filter_obj.filter_by_length([])
        assert filtered == []
    
    def test_filter_by_orientation_horizontal_vertical(self, sample_angled_lines):
        """Test filtering by orientation (prefer horizontal/vertical)."""
        config = LineFilterConfig(
            prefer_horizontal_vertical=True,
            angle_tolerance=5.0
        )
        filter_obj = LineFilter(config)
        filtered = filter_obj.filter_by_orientation(sample_angled_lines)
        
        # Should keep horizontal and vertical lines
        # Slight angle (5.7 degrees) may be filtered if tolerance is strict
        # Steep angle (26.6 degrees) should definitely be filtered
        assert len(filtered) >= 2  # At least horizontal and vertical
        # Verify horizontal and vertical are kept
        assert (0.0, 0.0, 100.0, 0.0) in filtered  # Horizontal
        assert (0.0, 0.0, 0.0, 100.0) in filtered  # Vertical
    
    def test_filter_by_orientation_all_angles(self, sample_angled_lines):
        """Test filtering with orientation preference disabled."""
        config = LineFilterConfig(prefer_horizontal_vertical=False)
        filter_obj = LineFilter(config)
        filtered = filter_obj.filter_by_orientation(sample_angled_lines)
        
        # Should keep all lines
        assert len(filtered) == len(sample_angled_lines)
    
    def test_group_parallel_lines(self):
        """Test grouping parallel lines."""
        lines = [
            (0.0, 0.0, 100.0, 0.0),      # Horizontal
            (0.0, 10.0, 100.0, 10.0),    # Parallel horizontal (close)
            (0.0, 20.0, 100.0, 20.0),    # Parallel horizontal (farther)
            (0.0, 0.0, 0.0, 100.0),      # Vertical (different angle)
        ]
        
        config = LineFilterConfig(group_parallel_threshold=15.0)
        filter_obj = LineFilter(config)
        grouped = filter_obj.group_parallel_lines(lines)
        
        # Should group first two horizontal lines (within threshold)
        # Third horizontal line might be grouped or separate depending on algorithm
        # Vertical line should remain separate
        assert len(grouped) <= len(lines)
        assert len(grouped) >= 2  # At least vertical and some horizontal
    
    def test_remove_duplicates(self):
        """Test removing duplicate lines."""
        lines = [
            (0.0, 0.0, 100.0, 0.0),
            (0.0, 0.0, 100.0, 0.0),      # Exact duplicate
            (1.0, 0.0, 101.0, 0.0),      # Very close duplicate
            (0.0, 0.0, 0.0, 100.0),      # Different line
        ]
        
        config = LineFilterConfig(remove_duplicates=True)
        filter_obj = LineFilter(config)
        unique = filter_obj.remove_duplicates(lines)
        
        # Should remove duplicates, keep at least 2 unique lines
        assert len(unique) >= 2
        assert len(unique) <= 3
    
    def test_remove_duplicates_disabled(self):
        """Test that duplicates are kept when disabled."""
        lines = [
            (0.0, 0.0, 100.0, 0.0),
            (0.0, 0.0, 100.0, 0.0),      # Duplicate
        ]
        
        config = LineFilterConfig(remove_duplicates=False)
        filter_obj = LineFilter(config)
        result = filter_obj.remove_duplicates(lines)
        
        assert len(result) == 2
    
    def test_filter_lines_full_pipeline(self, sample_lines):
        """Test full filtering pipeline."""
        config = LineFilterConfig(
            min_length=20.0,
            max_length=1000.0,
            prefer_horizontal_vertical=True
        )
        filter_obj = LineFilter(config)
        filtered = filter_obj.filter_lines(sample_lines)
        
        # Should apply all filters
        assert len(filtered) <= len(sample_lines)
        assert len(filtered) > 0
    
    def test_convert_to_wall_segments_no_normalization(self):
        """Test converting lines to wall segments without normalization."""
        lines = [
            (0.0, 0.0, 100.0, 0.0),
            (0.0, 0.0, 0.0, 50.0),
        ]
        
        filter_obj = LineFilter()
        segments = filter_obj.convert_to_wall_segments(lines)
        
        assert len(segments) == 2
        assert segments[0]['type'] == 'line'
        assert segments[0]['start'] == [0.0, 0.0]
        assert segments[0]['end'] == [100.0, 0.0]
        assert segments[0]['is_load_bearing'] is False
    
    def test_convert_to_wall_segments_with_normalization(self):
        """Test converting lines to wall segments with normalization."""
        lines = [
            (0.0, 0.0, 100.0, 0.0),      # In 200x200 image
            (0.0, 0.0, 0.0, 50.0),
        ]
        
        filter_obj = LineFilter()
        segments = filter_obj.convert_to_wall_segments(lines, image_width=200, image_height=200)
        
        assert len(segments) == 2
        # First line: x from 0-100 in 200px image = 0-500 in normalized
        assert segments[0]['start'] == [0.0, 0.0]
        assert segments[0]['end'] == [500.0, 0.0]
        # Second line: y from 0-50 in 200px image = 0-250 in normalized
        assert segments[1]['start'] == [0.0, 0.0]
        assert segments[1]['end'] == [0.0, 250.0]
    
    def test_convert_to_wall_segments_clamping(self):
        """Test that coordinates are clamped to 0-1000 range."""
        lines = [
            (-10.0, -10.0, 1100.0, 1100.0),  # Out of range
        ]
        
        filter_obj = LineFilter()
        segments = filter_obj.convert_to_wall_segments(lines, image_width=100, image_height=100)
        
        assert len(segments) == 1
        # Coordinates should be clamped
        assert 0.0 <= segments[0]['start'][0] <= 1000.0
        assert 0.0 <= segments[0]['start'][1] <= 1000.0
        assert 0.0 <= segments[0]['end'][0] <= 1000.0
        assert 0.0 <= segments[0]['end'][1] <= 1000.0


class TestConvenienceFunction:
    """Test convenience function filter_and_convert_lines."""
    
    def test_filter_and_convert_default(self, sample_lines):
        """Test convenience function with default config."""
        segments = filter_and_convert_lines(sample_lines)
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        assert all('type' in seg for seg in segments)
        assert all('start' in seg for seg in segments)
        assert all('end' in seg for seg in segments)
    
    def test_filter_and_convert_with_normalization(self, sample_lines):
        """Test convenience function with normalization."""
        segments = filter_and_convert_lines(
            sample_lines,
            image_width=200,
            image_height=200
        )
        
        assert isinstance(segments, list)
        # Verify normalized coordinates
        for seg in segments:
            assert 0.0 <= seg['start'][0] <= 1000.0
            assert 0.0 <= seg['start'][1] <= 1000.0
            assert 0.0 <= seg['end'][0] <= 1000.0
            assert 0.0 <= seg['end'][1] <= 1000.0
    
    def test_filter_and_convert_custom_config(self, sample_lines):
        """Test convenience function with custom config."""
        config = LineFilterConfig(min_length=50.0)
        segments = filter_and_convert_lines(sample_lines, config=config)
        
        assert isinstance(segments, list)
        # Should filter out shorter lines
        assert len(segments) <= len(sample_lines)

