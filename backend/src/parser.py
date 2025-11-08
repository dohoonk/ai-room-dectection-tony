"""Parser for wall line segments from JSON input."""
import json
from typing import List, Dict, Any, Tuple


class WallSegment:
    """Represents a single wall line segment."""
    
    def __init__(self, start: Tuple[float, float], end: Tuple[float, float], 
                 is_load_bearing: bool = False):
        self.start = start
        self.end = end
        self.is_load_bearing = is_load_bearing
    
    def __repr__(self):
        return f"WallSegment(start={self.start}, end={self.end}, load_bearing={self.is_load_bearing})"


def parse_line_segments(json_data: str) -> List[WallSegment]:
    """
    Parse JSON string into list of WallSegment objects.
    
    Args:
        json_data: JSON string or file path containing wall line segments
        
    Returns:
        List of WallSegment objects
        
    Raises:
        ValueError: If JSON is invalid or data structure is incorrect
        FileNotFoundError: If json_data is a file path that doesn't exist
    """
    # Try to load from file if it's a path, otherwise parse as JSON string
    # First check if it looks like a file path (contains path separators or ends with .json)
    is_likely_file = '/' in json_data or '\\' in json_data or json_data.endswith('.json')
    
    if is_likely_file:
        try:
            with open(json_data, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {json_data}")
        except OSError as e:
            raise OSError(f"Error reading file {json_data}: {e}")
    else:
        # Try parsing as JSON string
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")
    
    if not isinstance(data, list):
        raise ValueError("JSON data must be an array of wall segments")
    
    if len(data) == 0:
        raise ValueError("JSON data contains no wall segments")
    
    segments = []
    for i, wall in enumerate(data):
        if not isinstance(wall, dict):
            raise ValueError(f"Wall segment {i} must be an object")
        
        # Validate required fields
        if 'type' not in wall:
            raise ValueError(f"Wall segment {i} missing 'type' field")
        if wall['type'] != 'line':
            raise ValueError(f"Wall segment {i} has unsupported type: {wall['type']}")
        
        if 'start' not in wall:
            raise ValueError(f"Wall segment {i} missing 'start' field")
        if 'end' not in wall:
            raise ValueError(f"Wall segment {i} missing 'end' field")
        
        # Validate coordinates
        start = wall['start']
        end = wall['end']
        
        if not isinstance(start, list) or len(start) != 2:
            raise ValueError(f"Wall segment {i} 'start' must be [x, y] array")
        if not isinstance(end, list) or len(end) != 2:
            raise ValueError(f"Wall segment {i} 'end' must be [x, y] array")
        
        try:
            start_coords = (float(start[0]), float(start[1]))
            end_coords = (float(end[0]), float(end[1]))
        except (ValueError, TypeError):
            raise ValueError(f"Wall segment {i} coordinates must be numbers")
        
        # Validate coordinate range (0-1000)
        for coord in [start_coords[0], start_coords[1], end_coords[0], end_coords[1]]:
            if not (0 <= coord <= 1000):
                raise ValueError(f"Wall segment {i} coordinates must be in range 0-1000")
        
        # Get load bearing status (default to False)
        is_load_bearing = wall.get('is_load_bearing', False)
        if not isinstance(is_load_bearing, bool):
            raise ValueError(f"Wall segment {i} 'is_load_bearing' must be boolean")
        
        segments.append(WallSegment(start_coords, end_coords, is_load_bearing))
    
    return segments

