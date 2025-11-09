"""
Validation module for PDF-extracted wall segments.

Validates that extracted segments form valid wall connections and can be
processed by the existing room detection algorithm.
"""

from typing import List, Dict, Tuple, Optional, Any
from .parser import WallSegment, parse_line_segments
from .room_detector import build_wall_graph, snap_endpoints
import networkx as nx
import math


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class SegmentValidator:
    """Validator for PDF-extracted wall segments."""
    
    def __init__(self, 
                 min_segment_length: float = 5.0,
                 min_segment_count: int = 3,
                 min_wall_density: float = 0.001,
                 max_isolated_ratio: float = 0.5,
                 connectivity_tolerance: float = 1.0):
        """
        Initialize validator with thresholds.
        
        Args:
            min_segment_length: Minimum segment length in normalized coordinates
            min_segment_count: Minimum number of segments required
            min_wall_density: Minimum wall density (total length / area)
            max_isolated_ratio: Maximum ratio of isolated segments to total segments
            connectivity_tolerance: Tolerance for endpoint snapping (same as room detector)
        """
        self.min_segment_length = min_segment_length
        self.min_segment_count = min_segment_count
        self.min_wall_density = min_wall_density
        self.max_isolated_ratio = max_isolated_ratio
        self.connectivity_tolerance = connectivity_tolerance
    
    def validate_segments(self, segments: List[WallSegment]) -> Dict[str, Any]:
        """
        Validate extracted segments.
        
        Args:
            segments: List of wall segments to validate
            
        Returns:
            Dictionary with validation results:
            - valid: bool - Whether segments pass validation
            - errors: List[str] - List of validation error messages
            - warnings: List[str] - List of validation warnings
            - stats: Dict - Statistics about segments (count, total_length, etc.)
            
        Raises:
            ValidationError: If validation fails with critical errors
        """
        errors = []
        warnings = []
        stats = self._calculate_stats(segments)
        
        # Check minimum segment count
        if len(segments) < self.min_segment_count:
            errors.append(
                f"Insufficient segments: {len(segments)} < {self.min_segment_count} minimum. "
                "Need at least 3 segments to form a room."
            )
        
        # Check minimum segment length
        short_segments = [s for s in segments if self._segment_length(s) < self.min_segment_length]
        if short_segments:
            warnings.append(
                f"Found {len(short_segments)} segments shorter than {self.min_segment_length} units. "
                "These may be annotations or noise."
            )
        
        # Check wall density
        if stats['total_length'] > 0 and stats['bounding_area'] > 0:
            density = stats['total_length'] / stats['bounding_area']
            if density < self.min_wall_density:
                warnings.append(
                    f"Low wall density: {density:.6f} < {self.min_wall_density} minimum. "
                    "This may indicate missing walls or incorrect extraction."
                )
        
        # Check connectivity
        connectivity_result = self._check_connectivity(segments)
        if not connectivity_result['is_connected']:
            isolated_count = connectivity_result['isolated_count']
            total_count = len(segments)
            isolated_ratio = isolated_count / total_count if total_count > 0 else 0
            
            if isolated_ratio > self.max_isolated_ratio:
                errors.append(
                    f"Too many isolated segments: {isolated_count}/{total_count} ({isolated_ratio:.1%}) "
                    f"are isolated. Maximum allowed: {self.max_isolated_ratio:.1%}. "
                    "Segments should form connected walls."
                )
            else:
                warnings.append(
                    f"Found {isolated_count} isolated segment(s). "
                    "These may be annotations or disconnected walls."
                )
        
        # Check if segments can form cycles (for room detection)
        if len(segments) >= self.min_segment_count:
            can_form_cycles = self._can_form_cycles(segments)
            if not can_form_cycles:
                warnings.append(
                    "Segments may not form closed cycles. "
                    "Room detection may not find any rooms."
                )
        
        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'stats': stats,
            'connectivity': connectivity_result
        }
    
    def _calculate_stats(self, segments: List[WallSegment]) -> Dict[str, Any]:
        """Calculate statistics about segments."""
        if not segments:
            return {
                'count': 0,
                'total_length': 0.0,
                'avg_length': 0.0,
                'min_length': 0.0,
                'max_length': 0.0,
                'bounding_box': None,
                'bounding_area': 0.0
            }
        
        lengths = [self._segment_length(s) for s in segments]
        total_length = sum(lengths)
        
        # Calculate bounding box
        all_x = []
        all_y = []
        for segment in segments:
            all_x.extend([segment.start[0], segment.end[0]])
            all_y.extend([segment.start[1], segment.end[1]])
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        bounding_area = (max_x - min_x) * (max_y - min_y) if (max_x > min_x and max_y > min_y) else 0.0
        
        return {
            'count': len(segments),
            'total_length': total_length,
            'avg_length': total_length / len(segments) if segments else 0.0,
            'min_length': min(lengths) if lengths else 0.0,
            'max_length': max(lengths) if lengths else 0.0,
            'bounding_box': (min_x, min_y, max_x, max_y),
            'bounding_area': bounding_area
        }
    
    def _segment_length(self, segment: WallSegment) -> float:
        """Calculate length of a segment."""
        dx = segment.end[0] - segment.start[0]
        dy = segment.end[1] - segment.start[1]
        return math.sqrt(dx*dx + dy*dy)
    
    def _check_connectivity(self, segments: List[WallSegment]) -> Dict[str, Any]:
        """
        Check if segments form a connected graph.
        
        Returns:
            Dictionary with connectivity information:
            - is_connected: bool - Whether all segments are connected
            - component_count: int - Number of connected components
            - isolated_count: int - Number of isolated segments
            - largest_component_size: int - Size of largest component
        """
        if not segments:
            return {
                'is_connected': False,
                'component_count': 0,
                'isolated_count': 0,
                'largest_component_size': 0
            }
        
        # Build graph
        graph = build_wall_graph(segments, tolerance=self.connectivity_tolerance)
        
        # Find connected components
        components = list(nx.connected_components(graph))
        component_count = len(components)
        
        # Count isolated segments (components with only 1 edge)
        isolated_count = 0
        for component in components:
            subgraph = graph.subgraph(component)
            if subgraph.number_of_edges() == 1:
                isolated_count += 1
        
        # Check if all segments are in one component
        is_connected = component_count == 1
        
        # Find largest component
        largest_component_size = max(len(c) for c in components) if components else 0
        
        return {
            'is_connected': is_connected,
            'component_count': component_count,
            'isolated_count': isolated_count,
            'largest_component_size': largest_component_size
        }
    
    def _can_form_cycles(self, segments: List[WallSegment]) -> bool:
        """
        Check if segments can potentially form cycles (closed regions).
        
        A graph can form cycles if:
        - It has at least 3 nodes
        - The largest component has at least 3 edges
        - Nodes have degree >= 2 (for simple cycles)
        """
        if len(segments) < 3:
            return False
        
        graph = build_wall_graph(segments, tolerance=self.connectivity_tolerance)
        
        # Need at least 3 nodes to form a cycle
        if len(graph.nodes()) < 3:
            return False
        
        # Check if largest component can form cycles
        components = list(nx.connected_components(graph))
        if not components:
            return False
        
        largest_component = max(components, key=len)
        subgraph = graph.subgraph(largest_component)
        
        # Need at least 3 edges to form a cycle
        if subgraph.number_of_edges() < 3:
            return False
        
        # Check if nodes have sufficient degree (at least 2 for simple cycles)
        degrees = dict(subgraph.degree())
        nodes_with_degree_2_plus = sum(1 for d in degrees.values() if d >= 2)
        
        # Need at least 3 nodes with degree >= 2 to form a cycle
        return nodes_with_degree_2_plus >= 3


def validate_pdf_segments(segments: List[WallSegment], 
                          strict: bool = False) -> Dict[str, Any]:
    """
    Convenience function to validate PDF-extracted segments.
    
    Args:
        segments: List of wall segments to validate
        strict: If True, raises ValidationError on any errors. If False, returns results.
        
    Returns:
        Validation results dictionary (see SegmentValidator.validate_segments)
        
    Raises:
        ValidationError: If strict=True and validation fails
    """
    validator = SegmentValidator()
    results = validator.validate_segments(segments)
    
    if strict and not results['valid']:
        error_msg = "Validation failed:\n" + "\n".join(results['errors'])
        raise ValidationError(error_msg)
    
    return results

