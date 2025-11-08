"""Comprehensive unit tests for the line segment parser."""
import pytest
import json
import tempfile
import os
from src.parser import parse_line_segments, WallSegment


class TestValidJSONParsing:
    """Test cases for valid JSON parsing."""
    
    def test_parse_simple_valid_json(self):
        """Test parsing a simple valid JSON with one wall segment."""
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0],
            "end": [100.0, 100.0],
            "is_load_bearing": False
        }]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 1
        assert segments[0].start == (0.0, 0.0)
        assert segments[0].end == (100.0, 100.0)
        assert segments[0].is_load_bearing == False
    
    def test_parse_multiple_segments(self):
        """Test parsing JSON with multiple wall segments."""
        json_data = [
            {
                "type": "line",
                "start": [0.0, 0.0],
                "end": [100.0, 0.0],
                "is_load_bearing": True
            },
            {
                "type": "line",
                "start": [100.0, 0.0],
                "end": [100.0, 100.0],
                "is_load_bearing": False
            }
        ]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 2
        assert segments[0].is_load_bearing == True
        assert segments[1].is_load_bearing == False
    
    def test_parse_from_file_path(self):
        """Test parsing from a file path."""
        json_data = [{
            "type": "line",
            "start": [50.0, 50.0],
            "end": [150.0, 150.0],
            "is_load_bearing": False
        }]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name
        
        try:
            segments = parse_line_segments(temp_path)
            assert len(segments) == 1
            assert segments[0].start == (50.0, 50.0)
        finally:
            os.unlink(temp_path)
    
    def test_parse_with_default_load_bearing(self):
        """Test that is_load_bearing defaults to False when not provided."""
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0],
            "end": [100.0, 100.0]
        }]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 1
        assert segments[0].is_load_bearing == False
    
    def test_parse_coordinate_types(self):
        """Test that coordinates can be integers or floats."""
        json_data = [
            {
                "type": "line",
                "start": [0, 0],  # integers
                "end": [100, 100],
                "is_load_bearing": False
            },
            {
                "type": "line",
                "start": [0.5, 0.5],  # floats
                "end": [100.5, 100.5],
                "is_load_bearing": False
            }
        ]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 2
        assert segments[0].start == (0.0, 0.0)
        assert segments[1].start == (0.5, 0.5)


class TestInvalidJSONHandling:
    """Test cases for invalid JSON handling."""
    
    def test_invalid_json_string(self):
        """Test handling of malformed JSON string."""
        with pytest.raises(ValueError, match="Invalid JSON string"):
            parse_line_segments("{ invalid json }")
    
    def test_missing_type_field(self):
        """Test error when type field is missing."""
        json_data = [{
            "start": [0.0, 0.0],
            "end": [100.0, 100.0]
        }]
        
        with pytest.raises(ValueError, match="missing 'type' field"):
            parse_line_segments(json.dumps(json_data))
    
    def test_unsupported_type(self):
        """Test error when type is not 'line'."""
        json_data = [{
            "type": "arc",
            "start": [0.0, 0.0],
            "end": [100.0, 100.0]
        }]
        
        with pytest.raises(ValueError, match="unsupported type"):
            parse_line_segments(json.dumps(json_data))
    
    def test_missing_start_field(self):
        """Test error when start field is missing."""
        json_data = [{
            "type": "line",
            "end": [100.0, 100.0]
        }]
        
        with pytest.raises(ValueError, match="missing 'start' field"):
            parse_line_segments(json.dumps(json_data))
    
    def test_missing_end_field(self):
        """Test error when end field is missing."""
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0]
        }]
        
        with pytest.raises(ValueError, match="missing 'end' field"):
            parse_line_segments(json.dumps(json_data))
    
    def test_invalid_start_format(self):
        """Test error when start is not a 2-element array."""
        json_data = [{
            "type": "line",
            "start": [0.0],  # Only one coordinate
            "end": [100.0, 100.0]
        }]
        
        with pytest.raises(ValueError, match="'start' must be \\[x, y\\] array"):
            parse_line_segments(json.dumps(json_data))
    
    def test_invalid_end_format(self):
        """Test error when end is not a 2-element array."""
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0],
            "end": [100.0]  # Only one coordinate
        }]
        
        with pytest.raises(ValueError, match="'end' must be \\[x, y\\] array"):
            parse_line_segments(json.dumps(json_data))
    
    def test_invalid_coordinate_type(self):
        """Test error when coordinates are not numbers."""
        json_data = [{
            "type": "line",
            "start": ["0", "end"],  # String instead of number
            "end": [100.0, 100.0]
        }]
        
        with pytest.raises(ValueError, match="coordinates must be numbers"):
            parse_line_segments(json.dumps(json_data))
    
    def test_coordinate_out_of_range(self):
        """Test error when coordinates are outside 0-1000 range."""
        json_data = [{
            "type": "line",
            "start": [-10.0, 0.0],  # Negative
            "end": [100.0, 100.0]
        }]
        
        with pytest.raises(ValueError, match="coordinates must be in range 0-1000"):
            parse_line_segments(json.dumps(json_data))
        
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0],
            "end": [1001.0, 100.0]  # Too large
        }]
        
        with pytest.raises(ValueError, match="coordinates must be in range 0-1000"):
            parse_line_segments(json.dumps(json_data))
    
    def test_invalid_load_bearing_type(self):
        """Test error when is_load_bearing is not boolean."""
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0],
            "end": [100.0, 100.0],
            "is_load_bearing": "yes"  # String instead of boolean
        }]
        
        with pytest.raises(ValueError, match="'is_load_bearing' must be boolean"):
            parse_line_segments(json.dumps(json_data))


class TestEdgeCases:
    """Test cases for edge cases."""
    
    def test_empty_array(self):
        """Test error when JSON contains empty array."""
        json_data = []
        
        with pytest.raises(ValueError, match="contains no wall segments"):
            parse_line_segments(json.dumps(json_data))
    
    def test_non_array_root(self):
        """Test error when root is not an array."""
        json_data = {
            "type": "line",
            "start": [0.0, 0.0],
            "end": [100.0, 100.0]
        }
        
        with pytest.raises(ValueError, match="must be an array"):
            parse_line_segments(json.dumps(json_data))
    
    def test_non_object_segment(self):
        """Test error when segment is not an object."""
        json_data = ["not an object"]
        
        with pytest.raises(ValueError, match="must be an object"):
            parse_line_segments(json.dumps(json_data))
    
    def test_nonexistent_file(self):
        """Test error when file path doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parse_line_segments("/nonexistent/path/file.json")
    
    def test_zero_length_segment(self):
        """Test parsing a segment with start and end at same point."""
        json_data = [{
            "type": "line",
            "start": [100.0, 100.0],
            "end": [100.0, 100.0],  # Same point
            "is_load_bearing": False
        }]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        # Should parse successfully (zero-length segments are valid)
        assert len(segments) == 1
        assert segments[0].start == segments[0].end
    
    def test_boundary_coordinates(self):
        """Test parsing coordinates at boundaries (0 and 1000)."""
        json_data = [{
            "type": "line",
            "start": [0.0, 0.0],
            "end": [1000.0, 1000.0],
            "is_load_bearing": False
        }]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 1
        assert segments[0].start == (0.0, 0.0)
        assert segments[0].end == (1000.0, 1000.0)


class TestDataStructureOutput:
    """Test cases for verifying correct data structure output."""
    
    def test_wall_segment_structure(self):
        """Verify WallSegment has correct attributes."""
        json_data = [{
            "type": "line",
            "start": [10.0, 20.0],
            "end": [30.0, 40.0],
            "is_load_bearing": True
        }]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 1
        segment = segments[0]
        
        # Check attributes exist
        assert hasattr(segment, 'start')
        assert hasattr(segment, 'end')
        assert hasattr(segment, 'is_load_bearing')
        
        # Check types
        assert isinstance(segment.start, tuple)
        assert isinstance(segment.end, tuple)
        assert isinstance(segment.is_load_bearing, bool)
        
        # Check values
        assert segment.start == (10.0, 20.0)
        assert segment.end == (30.0, 40.0)
        assert segment.is_load_bearing == True
    
    def test_wall_segment_repr(self):
        """Verify WallSegment has useful string representation."""
        json_data = [{
            "type": "line",
            "start": [10.0, 20.0],
            "end": [30.0, 40.0],
            "is_load_bearing": True
        }]
        
        segments = parse_line_segments(json.dumps(json_data))
        segment = segments[0]
        
        repr_str = repr(segment)
        assert "WallSegment" in repr_str
        assert "start=" in repr_str
        assert "end=" in repr_str
    
    def test_multiple_segments_order(self):
        """Verify segments are returned in the same order as input."""
        json_data = [
            {
                "type": "line",
                "start": [0.0, 0.0],
                "end": [10.0, 0.0],
                "is_load_bearing": False
            },
            {
                "type": "line",
                "start": [10.0, 0.0],
                "end": [10.0, 10.0],
                "is_load_bearing": False
            },
            {
                "type": "line",
                "start": [10.0, 10.0],
                "end": [0.0, 10.0],
                "is_load_bearing": False
            }
        ]
        
        segments = parse_line_segments(json.dumps(json_data))
        
        assert len(segments) == 3
        assert segments[0].start == (0.0, 0.0)
        assert segments[1].start == (10.0, 0.0)
        assert segments[2].start == (10.0, 10.0)

