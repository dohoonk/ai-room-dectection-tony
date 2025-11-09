"""
Unit tests for PDF segment validation.
"""

import pytest
from src.pdf_validator import SegmentValidator, ValidationError, validate_pdf_segments
from src.parser import WallSegment


class TestSegmentValidator:
    """Test cases for segment validation."""
    
    def test_validate_sufficient_segments(self):
        """Test validation with sufficient segments."""
        validator = SegmentValidator(min_segment_count=3)
        
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (100, 100)),
            WallSegment((100, 100), (0, 100)),
            WallSegment((0, 100), (0, 0)),
        ]
        
        results = validator.validate_segments(segments)
        
        assert results['valid'] == True
        assert len(results['errors']) == 0
        assert results['stats']['count'] == 4
    
    def test_validate_insufficient_segments(self):
        """Test validation fails with too few segments."""
        validator = SegmentValidator(min_segment_count=3)
        
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (100, 100)),
        ]
        
        results = validator.validate_segments(segments)
        
        assert results['valid'] == False
        assert len(results['errors']) > 0
        assert any('Insufficient segments' in err for err in results['errors'])
    
    def test_validate_short_segments(self):
        """Test validation detects short segments."""
        validator = SegmentValidator(min_segment_length=10.0)
        
        segments = [
            WallSegment((0, 0), (5, 0)),  # Too short
            WallSegment((0, 0), (100, 0)),  # Long enough
            WallSegment((100, 0), (100, 100)),
            WallSegment((100, 100), (0, 100)),
            WallSegment((0, 100), (0, 0)),
        ]
        
        results = validator.validate_segments(segments)
        
        # Should have warning about short segments
        assert any('shorter than' in w for w in results['warnings'])
    
    def test_validate_connectivity(self):
        """Test validation checks connectivity."""
        validator = SegmentValidator()
        
        # Connected rectangle
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (100, 100)),
            WallSegment((100, 100), (0, 100)),
            WallSegment((0, 100), (0, 0)),
        ]
        
        results = validator.validate_segments(segments)
        
        assert results['connectivity']['is_connected'] == True
        assert results['connectivity']['component_count'] == 1
    
    def test_validate_isolated_segments(self):
        """Test validation detects isolated segments."""
        validator = SegmentValidator(max_isolated_ratio=0.3)
        
        # Connected rectangle + isolated segment
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (100, 100)),
            WallSegment((100, 100), (0, 100)),
            WallSegment((0, 100), (0, 0)),
            WallSegment((200, 200), (300, 300)),  # Isolated
        ]
        
        results = validator.validate_segments(segments)
        
        assert results['connectivity']['is_connected'] == False
        assert results['connectivity']['isolated_count'] == 1
        # Should have warning (not error) since ratio is acceptable
        assert any('isolated' in w.lower() for w in results['warnings'])
    
    def test_validate_too_many_isolated(self):
        """Test validation fails with too many isolated segments."""
        validator = SegmentValidator(max_isolated_ratio=0.3)
        
        # Mostly isolated segments
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (100, 100)),
            WallSegment((200, 200), (300, 300)),  # Isolated
            WallSegment((400, 400), (500, 500)),  # Isolated
            WallSegment((600, 600), (700, 700)),  # Isolated
        ]
        
        results = validator.validate_segments(segments)
        
        # Should have error about too many isolated segments
        assert any('Too many isolated' in err for err in results['errors'])
    
    def test_validate_can_form_cycles(self):
        """Test validation checks if segments can form cycles."""
        validator = SegmentValidator()
        
        # Rectangle (can form cycle)
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (100, 100)),
            WallSegment((100, 100), (0, 100)),
            WallSegment((0, 100), (0, 0)),
        ]
        
        results = validator.validate_segments(segments)
        
        # Should not have warning about cycles
        assert not any('may not form closed cycles' in w for w in results['warnings'])
    
    def test_validate_cannot_form_cycles(self):
        """Test validation warns when segments cannot form cycles."""
        validator = SegmentValidator(min_segment_count=3)
        
        # Three segments in a line (cannot form cycle - need at least 3 nodes with degree >= 2)
        segments = [
            WallSegment((0, 0), (100, 0)),
            WallSegment((100, 0), (200, 0)),
            WallSegment((200, 0), (300, 0)),
        ]
        
        results = validator.validate_segments(segments)
        
        # Should have warning about cycles (line segments can't form closed cycles)
        assert any('may not form closed cycles' in w for w in results['warnings'])
    
    def test_validate_stats_calculation(self):
        """Test that statistics are calculated correctly."""
        validator = SegmentValidator()
        
        segments = [
            WallSegment((0, 0), (100, 0)),  # Length: 100
            WallSegment((100, 0), (100, 50)),  # Length: 50
        ]
        
        results = validator.validate_segments(segments)
        stats = results['stats']
        
        assert stats['count'] == 2
        assert stats['total_length'] == 150.0
        assert stats['avg_length'] == 75.0
        assert stats['min_length'] == 50.0
        assert stats['max_length'] == 100.0
        assert stats['bounding_box'] == (0, 0, 100, 50)
        assert stats['bounding_area'] == 5000.0
    
    def test_validate_empty_segments(self):
        """Test validation with empty segment list."""
        validator = SegmentValidator()
        
        results = validator.validate_segments([])
        
        assert results['valid'] == False
        assert len(results['errors']) > 0
        assert results['stats']['count'] == 0


class TestValidatePdfSegments:
    """Test cases for convenience function."""
    
    def test_validate_strict_mode(self):
        """Test strict mode raises ValidationError."""
        segments = [
            WallSegment((0, 0), (100, 0)),
        ]
        
        with pytest.raises(ValidationError):
            validate_pdf_segments(segments, strict=True)
    
    def test_validate_non_strict_mode(self):
        """Test non-strict mode returns results."""
        segments = [
            WallSegment((0, 0), (100, 0)),
        ]
        
        results = validate_pdf_segments(segments, strict=False)
        
        assert 'valid' in results
        assert 'errors' in results
        assert 'warnings' in results
        assert 'stats' in results

