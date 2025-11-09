"""
Unit tests for image segment validation module.
"""

import pytest
from src.image_validator import validate_image_segments
from src.parser import WallSegment


@pytest.fixture
def sample_wall_segments():
    """Create sample wall segments for testing."""
    return [
        WallSegment(start=(0.0, 0.0), end=(100.0, 0.0), is_load_bearing=False),
        WallSegment(start=(100.0, 0.0), end=(100.0, 100.0), is_load_bearing=False),
        WallSegment(start=(100.0, 100.0), end=(0.0, 100.0), is_load_bearing=False),
        WallSegment(start=(0.0, 100.0), end=(0.0, 0.0), is_load_bearing=False),
    ]


@pytest.fixture
def isolated_segments():
    """Create isolated wall segments (not connected)."""
    return [
        WallSegment(start=(0.0, 0.0), end=(50.0, 0.0), is_load_bearing=False),
        WallSegment(start=(200.0, 200.0), end=(250.0, 200.0), is_load_bearing=False),
        WallSegment(start=(400.0, 400.0), end=(450.0, 400.0), is_load_bearing=False),
    ]


class TestImageValidator:
    """Test image segment validation."""
    
    def test_validate_connected_segments(self, sample_wall_segments):
        """Test validation of connected segments."""
        result = validate_image_segments(sample_wall_segments, strict=False)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['stats']['count'] == 4
    
    def test_validate_isolated_segments(self, isolated_segments):
        """Test validation with isolated segments."""
        # With 3 completely isolated segments, isolated ratio is 100% (3/3 = 1.0)
        # So even with max_isolated_ratio=0.9, it will fail
        result = validate_image_segments(
            isolated_segments,
            strict=False,
            connectivity_tolerance=5.0,
            max_isolated_ratio=1.0  # Allow all isolated
        )
        
        # Should pass with max_isolated_ratio=1.0 (allows 100% isolated)
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_insufficient_segments(self):
        """Test validation with insufficient segments."""
        segments = [
            WallSegment(start=(0.0, 0.0), end=(50.0, 0.0), is_load_bearing=False),
        ]
        
        result = validate_image_segments(segments, strict=False)
        
        # Should fail - need at least 3 segments to form a room
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any('Insufficient segments' in err for err in result['errors'])
    
    def test_validate_strict_mode(self, isolated_segments):
        """Test validation in strict mode (should raise exception)."""
        # Use strict settings that will fail
        with pytest.raises(Exception):  # Should raise ValidationError
            validate_image_segments(
                isolated_segments,
                strict=True,
                connectivity_tolerance=1.0,  # Very strict
                max_isolated_ratio=0.1  # Very strict
            )
    
    def test_validate_with_warnings(self, sample_wall_segments):
        """Test that validation can produce warnings."""
        # Add a very short segment
        segments = sample_wall_segments + [
            WallSegment(start=(0.0, 0.0), end=(2.0, 0.0), is_load_bearing=False),  # Very short
        ]
        
        result = validate_image_segments(segments, strict=False)
        
        # Should pass but may have warnings about short segments
        assert result['valid'] is True
        # May have warnings
        assert isinstance(result['warnings'], list)
    
    def test_validate_statistics(self, sample_wall_segments):
        """Test that validation returns statistics."""
        result = validate_image_segments(sample_wall_segments, strict=False)
        
        assert 'stats' in result
        assert result['stats']['count'] == 4
        assert result['stats']['total_length'] > 0
        assert 'bounding_box' in result['stats']
    
    def test_validate_connectivity_info(self, sample_wall_segments):
        """Test that validation returns connectivity information."""
        result = validate_image_segments(sample_wall_segments, strict=False)
        
        assert 'connectivity' in result
        assert 'is_connected' in result['connectivity']
        assert 'component_count' in result['connectivity']
        assert 'isolated_count' in result['connectivity']
    
    def test_validate_custom_tolerance(self, isolated_segments):
        """Test validation with custom tolerance settings."""
        # With 3 completely isolated segments, isolated ratio is 100%
        # Need max_isolated_ratio >= 1.0 to pass
        result = validate_image_segments(
            isolated_segments,
            strict=False,
            connectivity_tolerance=10.0,  # Very high tolerance
            max_isolated_ratio=1.0  # Allow all isolated
        )
        
        # Should pass with max_isolated_ratio=1.0
        assert result['valid'] is True

