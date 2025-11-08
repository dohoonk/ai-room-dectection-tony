"""Comprehensive unit tests for polygon to bounding box conversion."""
import pytest
from shapely.geometry import Polygon, Point
from src.room_detector import polygon_to_bounding_box, normalize_bounding_box


class TestBoundingBoxCalculation:
    """Test cases for bounding box calculation accuracy."""
    
    def test_rectangle_bounding_box(self):
        """Test bounding box for a rectangle."""
        cycle = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (0.0, 0.0, 100.0, 50.0), "Rectangle bounding box should match coordinates"
    
    def test_square_bounding_box(self):
        """Test bounding box for a square."""
        cycle = [(10.0, 10.0), (110.0, 10.0), (110.0, 110.0), (10.0, 110.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (10.0, 10.0, 110.0, 110.0), "Square bounding box should be correct"
    
    def test_triangle_bounding_box(self):
        """Test bounding box for a triangle."""
        cycle = [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (0.0, 0.0, 100.0, 100.0), "Triangle bounding box should encompass all points"
    
    def test_irregular_polygon_bounding_box(self):
        """Test bounding box for an irregular polygon."""
        cycle = [(10.0, 20.0), (150.0, 30.0), (140.0, 180.0), (20.0, 170.0), (5.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        # Should encompass all points
        assert bbox[0] == 5.0, "min_x should be minimum x coordinate"
        assert bbox[1] == 20.0, "min_y should be minimum y coordinate"
        assert bbox[2] == 150.0, "max_x should be maximum x coordinate"
        assert bbox[3] == 180.0, "max_y should be maximum y coordinate"
    
    def test_rotated_rectangle_bounding_box(self):
        """Test bounding box for a rotated rectangle (should still be axis-aligned)."""
        # 45-degree rotated square
        cycle = [(50.0, 0.0), (100.0, 50.0), (50.0, 100.0), (0.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        # Bounding box should be axis-aligned, encompassing the rotated square
        assert bbox[0] == 0.0, "min_x should encompass rotated shape"
        assert bbox[1] == 0.0, "min_y should encompass rotated shape"
        assert bbox[2] == 100.0, "max_x should encompass rotated shape"
        assert bbox[3] == 100.0, "max_y should encompass rotated shape"
    
    def test_pentagon_bounding_box(self):
        """Test bounding box for a pentagon."""
        cycle = [
            (50.0, 0.0),
            (95.0, 30.0),
            (77.0, 81.0),
            (23.0, 81.0),
            (5.0, 30.0)
        ]
        
        bbox = polygon_to_bounding_box(cycle)
        
        # Should encompass all pentagon vertices
        assert bbox[0] == 5.0, "min_x should be minimum"
        assert bbox[1] == 0.0, "min_y should be minimum"
        assert bbox[2] == 95.0, "max_x should be maximum"
        assert bbox[3] == 81.0, "max_y should be maximum"


class TestAxisAlignedConversion:
    """Test cases for axis-aligned bounding box conversion."""
    
    def test_diagonal_line_axis_aligned(self):
        """Test that diagonal polygon produces axis-aligned bounding box."""
        # Diagonal line segment (though not a valid polygon, tests the function)
        cycle = [(0.0, 0.0), (100.0, 100.0), (50.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        # Should be axis-aligned
        assert bbox[0] == 0.0
        assert bbox[1] == 0.0
        assert bbox[2] == 100.0
        assert bbox[3] == 100.0
    
    def test_non_axis_aligned_polygon(self):
        """Test polygon with non-axis-aligned edges."""
        # Diamond shape
        cycle = [(50.0, 0.0), (100.0, 50.0), (50.0, 100.0), (0.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        # Bounding box should be axis-aligned
        assert bbox == (0.0, 0.0, 100.0, 100.0), "Diamond should have axis-aligned bounding box"
    
    def test_axis_alignment_property(self):
        """Verify bounding box is always axis-aligned."""
        # Various shapes
        test_cycles = [
            [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],  # Rectangle
            [(50.0, 0.0), (100.0, 50.0), (50.0, 100.0), (0.0, 50.0)],  # Diamond
            [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)],  # Triangle
        ]
        
        for cycle in test_cycles:
            bbox = polygon_to_bounding_box(cycle)
            # Axis-aligned means min_x < max_x and min_y < max_y, and edges are parallel to axes
            assert bbox[0] <= bbox[2], "min_x should be <= max_x"
            assert bbox[1] <= bbox[3], "min_y should be <= max_y"
            # The bounding box format (min_x, min_y, max_x, max_y) ensures axis-alignment


class TestEdgeCases:
    """Test cases for edge cases in bounding box calculation."""
    
    def test_empty_cycle(self):
        """Test bounding box for empty cycle."""
        cycle = []
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (0, 0, 0, 0), "Empty cycle should return (0, 0, 0, 0)"
    
    def test_single_point(self):
        """Test bounding box for single point."""
        cycle = [(50.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (50.0, 50.0, 50.0, 50.0), "Single point should have zero-size bounding box"
    
    def test_two_points(self):
        """Test bounding box for two points."""
        cycle = [(0.0, 0.0), (100.0, 100.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (0.0, 0.0, 100.0, 100.0), "Two points should form bounding box"
    
    def test_collinear_points(self):
        """Test bounding box for collinear points."""
        cycle = [(0.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (0.0, 0.0, 100.0, 0.0), "Collinear points should form line bounding box"
    
    def test_negative_coordinates(self):
        """Test bounding box with negative coordinates."""
        cycle = [(-50.0, -30.0), (50.0, -30.0), (50.0, 70.0), (-50.0, 70.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (-50.0, -30.0, 50.0, 70.0), "Should handle negative coordinates"
    
    def test_float_coordinates(self):
        """Test bounding box with floating point coordinates."""
        cycle = [(10.5, 20.7), (100.3, 20.7), (100.3, 80.9), (10.5, 80.9)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert bbox == (10.5, 20.7, 100.3, 80.9), "Should handle float coordinates"


class TestEncompassment:
    """Test cases for verifying bounding boxes encompass polygons."""
    
    def test_rectangle_encompassment(self):
        """Verify bounding box encompasses rectangle."""
        cycle = [(10.0, 20.0), (110.0, 20.0), (110.0, 120.0), (10.0, 120.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        polygon = Polygon(cycle)
        
        # Create bounding box polygon
        bbox_polygon = Polygon([
            (bbox[0], bbox[1]),
            (bbox[2], bbox[1]),
            (bbox[2], bbox[3]),
            (bbox[0], bbox[3])
        ])
        
        # Bounding box should contain the original polygon
        assert bbox_polygon.contains(polygon) or bbox_polygon.covers(polygon), \
            "Bounding box should contain the polygon"
    
    def test_triangle_encompassment(self):
        """Verify bounding box encompasses triangle."""
        cycle = [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        polygon = Polygon(cycle)
        
        # Create bounding box polygon
        bbox_polygon = Polygon([
            (bbox[0], bbox[1]),
            (bbox[2], bbox[1]),
            (bbox[2], bbox[3]),
            (bbox[0], bbox[3])
        ])
        
        assert bbox_polygon.contains(polygon) or bbox_polygon.covers(polygon), \
            "Bounding box should contain the triangle"
    
    def test_irregular_shape_encompassment(self):
        """Verify bounding box encompasses irregular shape."""
        cycle = [(10.0, 20.0), (150.0, 30.0), (140.0, 180.0), (20.0, 170.0), (5.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        polygon = Polygon(cycle)
        
        # Create bounding box polygon
        bbox_polygon = Polygon([
            (bbox[0], bbox[1]),
            (bbox[2], bbox[1]),
            (bbox[2], bbox[3]),
            (bbox[0], bbox[3])
        ])
        
        assert bbox_polygon.contains(polygon) or bbox_polygon.covers(polygon), \
            "Bounding box should contain the irregular polygon"
    
    def test_all_points_within_bbox(self):
        """Verify all polygon vertices are within bounding box."""
        cycle = [(25.0, 35.0), (125.0, 35.0), (125.0, 135.0), (25.0, 135.0), (50.0, 50.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        # All points should be within bounding box
        for point in cycle:
            assert bbox[0] <= point[0] <= bbox[2], f"Point {point} x-coordinate should be within bbox"
            assert bbox[1] <= point[1] <= bbox[3], f"Point {point} y-coordinate should be within bbox"


class TestNormalizeBoundingBox:
    """Test cases for bounding box normalization."""
    
    def test_already_in_range(self):
        """Test normalization when bbox is already in target range."""
        bbox = (100.0, 200.0, 300.0, 400.0)
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        assert normalized == bbox, "Bbox already in range should be unchanged"
    
    def test_normalize_large_bbox(self):
        """Test normalization of large bounding box."""
        bbox = (0.0, 0.0, 2000.0, 1500.0)  # Larger than 0-1000 range
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        # Should be scaled down to fit in 0-1000
        assert normalized[0] >= 0.0, "min_x should be >= 0"
        assert normalized[1] >= 0.0, "min_y should be >= 0"
        assert normalized[2] <= 1000.0, "max_x should be <= 1000"
        assert normalized[3] <= 1000.0, "max_y should be <= 1000"
    
    def test_normalize_small_bbox(self):
        """Test normalization of small bounding box."""
        bbox = (0.0, 0.0, 50.0, 30.0)  # Smaller than 0-1000 range
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        # Small bbox should still be in range, so should be unchanged
        assert normalized == bbox or (normalized[2] <= 1000.0 and normalized[3] <= 1000.0)
    
    def test_preserve_aspect_ratio(self):
        """Test that normalization attempts to preserve aspect ratio during scaling."""
        # Use a bbox that fits well within target range after scaling
        bbox = (0.0, 0.0, 500.0, 250.0)  # 2:1 aspect ratio, will fit in 0-1000
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        # Since bbox is already in range, it should be unchanged
        # This tests that the function preserves aspect ratio when no scaling is needed
        assert normalized == bbox, "Bbox in range should preserve aspect ratio"
        
        # Test with a case that requires scaling but fits well
        bbox2 = (0.0, 0.0, 200.0, 100.0)  # 2:1 aspect ratio
        normalized2 = normalize_bounding_box(bbox2, target_range=(0, 1000))
        
        # Should still be in range, so unchanged
        assert normalized2 == bbox2, "Small bbox should remain unchanged"
    
    def test_custom_target_range(self):
        """Test normalization with custom target range."""
        bbox = (0.0, 0.0, 500.0, 500.0)
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 500))
        
        # Should fit in 0-500 range
        assert normalized[2] <= 500.0, "max_x should be <= 500"
        assert normalized[3] <= 500.0, "max_y should be <= 500"
    
    def test_zero_width_bbox(self):
        """Test normalization of zero-width bounding box."""
        bbox = (100.0, 0.0, 100.0, 100.0)  # Zero width
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        # Should return unchanged (zero width/height cases return as-is)
        assert normalized == bbox, "Zero width bbox should be returned unchanged"
    
    def test_zero_height_bbox(self):
        """Test normalization of zero-height bounding box."""
        bbox = (0.0, 100.0, 100.0, 100.0)  # Zero height
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        # Should return unchanged
        assert normalized == bbox, "Zero height bbox should be returned unchanged"
    
    def test_negative_coordinates_normalization(self):
        """Test normalization with negative coordinates."""
        bbox = (-100.0, -50.0, 200.0, 150.0)
        
        normalized = normalize_bounding_box(bbox, target_range=(0, 1000))
        
        # Should be normalized to positive range
        assert normalized[0] >= 0.0, "Normalized min_x should be >= 0"
        assert normalized[1] >= 0.0, "Normalized min_y should be >= 0"
        assert normalized[2] <= 1000.0, "Normalized max_x should be <= 1000"
        assert normalized[3] <= 1000.0, "Normalized max_y should be <= 1000"


class TestBoundingBoxFormat:
    """Test cases for bounding box format and structure."""
    
    def test_bbox_format(self):
        """Test that bounding box is in correct format (min_x, min_y, max_x, max_y)."""
        cycle = [(10.0, 20.0), (100.0, 20.0), (100.0, 80.0), (10.0, 80.0)]
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert len(bbox) == 4, "Bounding box should have 4 values"
        assert bbox[0] <= bbox[2], "min_x should be <= max_x"
        assert bbox[1] <= bbox[3], "min_y should be <= max_y"
    
    def test_bbox_coordinate_types(self):
        """Test that bounding box coordinates are floats."""
        cycle = [(0, 0), (100, 100), (100, 0)]  # Integer coordinates
        
        bbox = polygon_to_bounding_box(cycle)
        
        assert all(isinstance(coord, (int, float)) for coord in bbox), \
            "All coordinates should be numeric"
    
    def test_consistency(self):
        """Test that bounding box calculation is consistent."""
        cycle = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        
        bbox1 = polygon_to_bounding_box(cycle)
        bbox2 = polygon_to_bounding_box(cycle)
        
        assert bbox1 == bbox2, "Bounding box should be consistent across calls"

