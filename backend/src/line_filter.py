"""
Line filtering and segment conversion module for raster blueprint processing.

Filters detected lines and converts them to wall segment format compatible
with the existing room detection algorithm.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import math
from .parser import WallSegment


@dataclass
class LineFilterConfig:
    """Configuration for line filtering."""
    min_length: float = 20.0  # Minimum line length in pixels
    max_length: float = 10000.0  # Maximum line length in pixels
    prefer_horizontal_vertical: bool = True  # Prefer horizontal/vertical lines
    angle_tolerance: float = 5.0  # Degrees tolerance for horizontal/vertical
    group_parallel_threshold: float = 2.0  # Pixels - lines closer than this are grouped
    remove_duplicates: bool = True  # Remove duplicate or very similar lines


class LineFilter:
    """Filter and process detected lines."""
    
    def __init__(self, config: Optional[LineFilterConfig] = None):
        """
        Initialize line filter.
        
        Args:
            config: Filtering configuration. If None, uses defaults.
        """
        self.config = config or LineFilterConfig()
    
    def filter_by_length(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        """
        Filter lines by minimum and maximum length.
        
        Args:
            lines: List of lines as (x1, y1, x2, y2) tuples
            
        Returns:
            Filtered list of lines
        """
        filtered = []
        for line in lines:
            x1, y1, x2, y2 = line
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            if self.config.min_length <= length <= self.config.max_length:
                filtered.append(line)
        
        return filtered
    
    def filter_by_orientation(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        """
        Filter lines by orientation (prefer horizontal/vertical if enabled).
        
        Args:
            lines: List of lines as (x1, y1, x2, y2) tuples
            
        Returns:
            Filtered list of lines
        """
        if not self.config.prefer_horizontal_vertical:
            return lines
        
        filtered = []
        tolerance_rad = math.radians(self.config.angle_tolerance)
        
        for line in lines:
            x1, y1, x2, y2 = line
            dx = x2 - x1
            dy = y2 - y1
            
            if abs(dx) < 1e-6:  # Vertical line
                filtered.append(line)
            elif abs(dy) < 1e-6:  # Horizontal line
                filtered.append(line)
            else:
                # Check angle from horizontal or vertical
                angle = math.atan2(abs(dy), abs(dx))
                angle_from_horizontal = angle
                angle_from_vertical = abs(angle - math.pi / 2)
                
                if (angle_from_horizontal <= tolerance_rad or 
                    angle_from_vertical <= tolerance_rad):
                    filtered.append(line)
        
        return filtered
    
    def group_parallel_lines(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        """
        Group nearby parallel lines and merge them.
        
        Args:
            lines: List of lines as (x1, y1, x2, y2) tuples
            
        Returns:
            List of grouped/merged lines
        """
        if not lines:
            return []
        
        # Group lines by similar angle
        angle_groups = {}
        threshold = self.config.group_parallel_threshold
        
        for line in lines:
            x1, y1, x2, y2 = line
            dx = x2 - x1
            dy = y2 - y1
            
            # Calculate angle (normalize to 0-180 degrees)
            angle = math.degrees(math.atan2(dy, dx)) % 180
            
            # Find existing group with similar angle
            grouped = False
            for group_angle in angle_groups.keys():
                angle_diff = abs(angle - group_angle)
                if angle_diff <= 5.0 or angle_diff >= 175.0:  # Within 5 degrees or opposite
                    angle_groups[group_angle].append(line)
                    grouped = True
                    break
            
            if not grouped:
                angle_groups[angle] = [line]
        
        # Merge lines in each group
        merged_lines = []
        for group_lines in angle_groups.values():
            if len(group_lines) == 1:
                merged_lines.append(group_lines[0])
            else:
                # Merge nearby parallel lines
                merged = self._merge_parallel_lines(group_lines, threshold)
                merged_lines.extend(merged)
        
        return merged_lines
    
    def _merge_parallel_lines(self, lines: List[Tuple[float, float, float, float]], 
                             threshold: float) -> List[Tuple[float, float, float, float]]:
        """
        Merge nearby parallel lines.
        
        Args:
            lines: List of parallel lines
            threshold: Distance threshold for merging
            
        Returns:
            List of merged lines
        """
        if len(lines) <= 1:
            return lines
        
        merged = []
        used = set()
        
        for i, line1 in enumerate(lines):
            if i in used:
                continue
            
            x1, y1, x2, y2 = line1
            group = [line1]
            used.add(i)
            
            # Find nearby parallel lines
            for j, line2 in enumerate(lines[i+1:], start=i+1):
                if j in used:
                    continue
                
                x3, y3, x4, y4 = line2
                
                # Check if lines are close enough to merge
                # Calculate distance between line midpoints
                mid1 = ((x1 + x2) / 2, (y1 + y2) / 2)
                mid2 = ((x3 + x4) / 2, (y3 + y4) / 2)
                distance = math.sqrt((mid1[0] - mid2[0])**2 + (mid1[1] - mid2[1])**2)
                
                if distance <= threshold:
                    group.append(line2)
                    used.add(j)
            
            # Merge lines in group
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Extend line to cover all points
                all_points = []
                for line in group:
                    all_points.extend([(line[0], line[1]), (line[2], line[3])])
                
                # Find bounding box and create line from min to max
                xs = [p[0] for p in all_points]
                ys = [p[1] for p in all_points]
                
                # Determine if line is more horizontal or vertical
                dx = max(xs) - min(xs)
                dy = max(ys) - min(ys)
                
                if dx > dy:  # More horizontal
                    y_avg = sum(ys) / len(ys)
                    merged.append((min(xs), y_avg, max(xs), y_avg))
                else:  # More vertical
                    x_avg = sum(xs) / len(xs)
                    merged.append((x_avg, min(ys), x_avg, max(ys)))
        
        return merged
    
    def remove_duplicates(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        """
        Remove duplicate or very similar lines.
        
        Args:
            lines: List of lines as (x1, y1, x2, y2) tuples
            
        Returns:
            List of unique lines
        """
        if not self.config.remove_duplicates:
            return lines
        
        unique_lines = []
        threshold = 2.0  # Pixels
        
        for line in lines:
            is_duplicate = False
            x1, y1, x2, y2 = line
            
            for unique_line in unique_lines:
                ux1, uy1, ux2, uy2 = unique_line
                
                # Check if endpoints are very close
                dist1 = math.sqrt((x1 - ux1)**2 + (y1 - uy1)**2)
                dist2 = math.sqrt((x2 - ux2)**2 + (y2 - uy2)**2)
                
                if dist1 <= threshold and dist2 <= threshold:
                    is_duplicate = True
                    break
                
                # Also check reversed endpoints
                dist1_rev = math.sqrt((x1 - ux2)**2 + (y1 - uy2)**2)
                dist2_rev = math.sqrt((x2 - ux1)**2 + (y2 - uy1)**2)
                
                if dist1_rev <= threshold and dist2_rev <= threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_lines.append(line)
        
        return unique_lines
    
    def filter_lines(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        """
        Apply all filtering steps to lines.
        
        Args:
            lines: List of lines as (x1, y1, x2, y2) tuples
            
        Returns:
            Filtered list of lines
        """
        filtered = lines
        
        # Filter by length
        filtered = self.filter_by_length(filtered)
        
        # Filter by orientation (if enabled)
        filtered = self.filter_by_orientation(filtered)
        
        # Group parallel lines
        filtered = self.group_parallel_lines(filtered)
        
        # Remove duplicates
        filtered = self.remove_duplicates(filtered)
        
        return filtered
    
    def convert_to_wall_segments(self, lines: List[Tuple[float, float, float, float]], 
                                 image_width: Optional[int] = None,
                                 image_height: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Convert filtered lines to wall segment format.
        
        Args:
            lines: List of filtered lines as (x1, y1, x2, y2) tuples
            image_width: Original image width (for normalization)
            image_height: Original image height (for normalization)
            
        Returns:
            List of wall segment dictionaries compatible with existing parser
        """
        wall_segments = []
        
        for line in lines:
            x1, y1, x2, y2 = line
            
            # Normalize coordinates to 0-1000 range if image dimensions provided
            if image_width and image_height:
                # Scale to 0-1000 range
                x1_norm = (x1 / image_width) * 1000.0
                y1_norm = (y1 / image_height) * 1000.0
                x2_norm = (x2 / image_width) * 1000.0
                y2_norm = (y2 / image_height) * 1000.0
                
                # Clamp to 0-1000 range
                x1_norm = max(0.0, min(1000.0, x1_norm))
                y1_norm = max(0.0, min(1000.0, y1_norm))
                x2_norm = max(0.0, min(1000.0, x2_norm))
                y2_norm = max(0.0, min(1000.0, y2_norm))
            else:
                # Use original coordinates (assume already normalized)
                x1_norm, y1_norm, x2_norm, y2_norm = x1, y1, x2, y2
            
            wall_segment = {
                "type": "line",
                "start": [x1_norm, y1_norm],
                "end": [x2_norm, y2_norm],
                "is_load_bearing": False  # Default, can be enhanced later
            }
            
            wall_segments.append(wall_segment)
        
        return wall_segments


def filter_and_convert_lines(lines: List[Tuple[float, float, float, float]],
                            image_width: Optional[int] = None,
                            image_height: Optional[int] = None,
                            config: Optional[LineFilterConfig] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to filter lines and convert to wall segments.
    
    Args:
        lines: List of lines as (x1, y1, x2, y2) tuples
        image_width: Original image width (for normalization)
        image_height: Original image height (for normalization)
        config: Filtering configuration. If None, uses defaults.
        
    Returns:
        List of wall segment dictionaries
    """
    filter_obj = LineFilter(config)
    filtered_lines = filter_obj.filter_lines(lines)
    wall_segments = filter_obj.convert_to_wall_segments(
        filtered_lines,
        image_width,
        image_height
    )
    return wall_segments

