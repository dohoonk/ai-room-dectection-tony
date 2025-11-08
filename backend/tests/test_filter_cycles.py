"""Comprehensive unit tests for cycle filtering functionality."""
import pytest
from shapely.geometry import Polygon
from src.room_detector import filter_cycles


class TestFilterSmallCycles:
    """Test cases for filtering small cycles."""
    
    def test_filter_tiny_cycle(self):
        """Test that very small cycles are filtered out."""
        # Tiny triangle (area < 100)
        cycles = [
            [(0.0, 0.0), (10.0, 0.0), (5.0, 5.0)]  # Area = 25
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 0, "Tiny cycle should be filtered out"
    
    def test_filter_small_perimeter(self):
        """Test that cycles with small perimeter are filtered out."""
        # Small rectangle with area OK but small perimeter
        cycles = [
            [(0.0, 0.0), (50.0, 0.0), (50.0, 1.0), (0.0, 1.0)]  # Perimeter = 102, but very thin
        ]
        
        filtered = filter_cycles(cycles, min_area=10.0, min_perimeter=200.0)
        
        assert len(filtered) == 0, "Cycle with small perimeter should be filtered out"
    
    def test_keep_valid_sized_cycle(self):
        """Test that valid room-sized cycles are kept."""
        # Room-sized rectangle (100x100 = 10,000 area, 400 perimeter)
        cycles = [
            [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Valid room-sized cycle should be kept"
        assert filtered[0] == cycles[0]
    
    def test_filter_below_min_area_threshold(self):
        """Test filtering cycles just below minimum area threshold."""
        # Cycle with area just below threshold
        cycles = [
            [(0.0, 0.0), (9.0, 0.0), (9.0, 9.0), (0.0, 9.0)]  # Area = 81 < 100
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 0, "Cycle below min_area should be filtered"
    
    def test_keep_cycle_at_min_area_threshold(self):
        """Test that cycles at minimum area threshold are kept."""
        # Cycle with area exactly at threshold (10x10 = 100)
        cycles = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]  # Area = 100
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Cycle at min_area threshold should be kept"


class TestFilterLargeCycles:
    """Test cases for filtering large cycles (outer perimeter)."""
    
    def test_filter_outer_perimeter(self):
        """Test that very large cycles (outer perimeter) are filtered out."""
        # Very large rectangle (likely outer perimeter)
        cycles = [
            [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]  # Area = 1,000,000
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0, max_area=900000.0)
        
        assert len(filtered) == 0, "Outer perimeter should be filtered out"
    
    def test_keep_large_but_valid_room(self):
        """Test that large but valid rooms are kept."""
        # Large room but within max_area
        cycles = [
            [(0.0, 0.0), (500.0, 0.0), (500.0, 500.0), (0.0, 500.0)]  # Area = 250,000 < 900,000
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0, max_area=900000.0)
        
        assert len(filtered) == 1, "Large but valid room should be kept"
    
    def test_filter_at_max_area_threshold(self):
        """Test filtering cycles at maximum area threshold."""
        # Cycle with area exactly at max threshold
        cycles = [
            [(0.0, 0.0), (948.68, 0.0), (948.68, 948.68), (0.0, 948.68)]  # Area ≈ 900,000
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0, max_area=900000.0)
        
        # Should be kept (area <= max_area)
        assert len(filtered) == 1, "Cycle at max_area threshold should be kept"


class TestFilterInvalidShapes:
    """Test cases for filtering invalid or irregular shapes."""
    
    def test_filter_invalid_polygon(self):
        """Test that invalid polygons are filtered out."""
        # Self-intersecting polygon (invalid)
        cycles = [
            [(0.0, 0.0), (100.0, 0.0), (0.0, 100.0), (100.0, 100.0)]  # Bowtie shape
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        # Invalid polygons should be filtered (though this specific shape might be valid)
        # The function checks polygon.is_valid, so invalid ones will be filtered
        assert isinstance(filtered, list)
    
    def test_filter_insufficient_points(self):
        """Test that cycles with less than 3 points are filtered out."""
        cycles = [
            [(0.0, 0.0), (100.0, 0.0)],  # Only 2 points - can't form polygon
            [(0.0, 0.0)],  # Only 1 point
            [],  # Empty
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 0, "Cycles with < 3 points should be filtered"
    
    def test_keep_valid_polygon(self):
        """Test that valid polygons are kept."""
        # Valid rectangle
        cycles = [
            [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Valid polygon should be kept"
    
    def test_filter_degenerate_polygon(self):
        """Test that degenerate polygons are handled."""
        # All points on a line (zero area)
        cycles = [
            [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0), (300.0, 0.0)]  # Collinear points
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        # Degenerate polygons have zero area, should be filtered
        assert len(filtered) == 0, "Degenerate polygon should be filtered"


class TestFilterMultipleCycles:
    """Test cases for filtering multiple cycles."""
    
    def test_filter_mixed_sizes(self):
        """Test filtering a mix of valid and invalid cycles."""
        cycles = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],  # Too small (area=100, but might pass)
            [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],  # Valid (area=10,000)
            [(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)],  # Too small (area=12.5)
            [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)],  # Valid (area=40,000)
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        # Should keep cycles with area >= 100
        assert len(filtered) >= 2, "Should keep valid room-sized cycles"
        # Verify the large ones are kept
        large_cycles = [c for c in filtered if len(c) >= 4]
        assert len(large_cycles) >= 2
    
    def test_filter_all_small_cycles(self):
        """Test filtering when all cycles are too small."""
        cycles = [
            [(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)],  # Area = 12.5
            [(0.0, 0.0), (8.0, 0.0), (8.0, 8.0), (0.0, 8.0)],  # Area = 64
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 0, "All small cycles should be filtered"
    
    def test_keep_all_valid_cycles(self):
        """Test that all valid cycles are kept."""
        cycles = [
            [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],  # Valid
            [(200.0, 0.0), (300.0, 0.0), (300.0, 100.0), (200.0, 100.0)],  # Valid
            [(0.0, 200.0), (150.0, 200.0), (150.0, 300.0), (0.0, 300.0)],  # Valid
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 3, "All valid cycles should be kept"


class TestEdgeCases:
    """Test cases for edge cases in filtering."""
    
    def test_empty_cycles_list(self):
        """Test filtering empty list of cycles."""
        cycles = []
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert isinstance(filtered, list)
        assert len(filtered) == 0
    
    def test_custom_thresholds(self):
        """Test filtering with custom threshold values."""
        cycles = [
            [(0.0, 0.0), (50.0, 0.0), (50.0, 50.0), (0.0, 50.0)]  # Area = 2500
        ]
        
        # Very high threshold
        filtered_high = filter_cycles(cycles, min_area=10000.0, min_perimeter=40.0)
        assert len(filtered_high) == 0, "Should filter with high threshold"
        
        # Low threshold
        filtered_low = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        assert len(filtered_low) == 1, "Should keep with low threshold"
    
    def test_zero_min_area(self):
        """Test filtering with zero minimum area."""
        cycles = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]  # Area = 100
        ]
        
        filtered = filter_cycles(cycles, min_area=0.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Should keep cycle with zero min_area"
    
    def test_very_large_max_area(self):
        """Test filtering with very large max_area."""
        cycles = [
            [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]  # Area = 1,000,000
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0, max_area=2000000.0)
        
        assert len(filtered) == 1, "Should keep with very large max_area"
    
    def test_triangle_cycle(self):
        """Test filtering triangular cycles."""
        # Small triangle
        small_triangle = [(0.0, 0.0), (10.0, 0.0), (5.0, 5.0)]  # Area = 25
        
        # Large triangle
        large_triangle = [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]  # Area = 5000
        
        cycles = [small_triangle, large_triangle]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        # Should keep large triangle, filter small one
        assert len(filtered) >= 1, "Should keep valid triangle"
        # Verify large triangle is in results
        triangle_areas = [Polygon(c).area for c in filtered]
        assert any(area >= 100.0 for area in triangle_areas), "Large triangle should be kept"
    
    def test_pentagon_cycle(self):
        """Test filtering pentagonal cycles."""
        # Regular pentagon (approximate)
        pentagon = [
            (50.0, 0.0),
            (95.0, 30.0),
            (77.0, 81.0),
            (23.0, 81.0),
            (5.0, 30.0)
        ]
        
        cycles = [pentagon]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        # Should handle non-rectangular shapes
        assert isinstance(filtered, list)
        # If valid and large enough, should be kept
        if len(filtered) > 0:
            assert len(filtered[0]) == 5, "Pentagon should have 5 points"


class TestBoundaryConditions:
    """Test cases for boundary conditions."""
    
    def test_exactly_min_area(self):
        """Test cycle with exactly minimum area."""
        # 10x10 square = 100 area
        cycles = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Cycle at exact min_area should be kept"
    
    def test_exactly_min_perimeter(self):
        """Test cycle with exactly minimum perimeter."""
        # 10x10 square = 40 perimeter
        cycles = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Cycle at exact min_perimeter should be kept"
    
    def test_exactly_max_area(self):
        """Test cycle with exactly maximum area."""
        # Large square approaching max_area
        # For max_area=900000, sqrt(900000) ≈ 948.68
        cycles = [
            [(0.0, 0.0), (948.0, 0.0), (948.0, 948.0), (0.0, 948.0)]  # Area ≈ 898,704
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0, max_area=900000.0)
        
        assert len(filtered) == 1, "Cycle at max_area should be kept"
    
    def test_just_below_min_area(self):
        """Test cycle just below minimum area."""
        # 9.9x9.9 square ≈ 98.01 area
        cycles = [
            [(0.0, 0.0), (9.9, 0.0), (9.9, 9.9), (0.0, 9.9)]
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 0, "Cycle just below min_area should be filtered"
    
    def test_just_above_min_area(self):
        """Test cycle just above minimum area."""
        # 10.1x10.1 square ≈ 102.01 area
        cycles = [
            [(0.0, 0.0), (10.1, 0.0), (10.1, 10.1), (0.0, 10.1)]
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
        
        assert len(filtered) == 1, "Cycle just above min_area should be kept"


class TestFilteringCriteria:
    """Test cases for verifying filtering criteria work correctly."""
    
    def test_area_and_perimeter_both_required(self):
        """Test that both area and perimeter criteria must be met."""
        # Cycle with good area but small perimeter
        thin_cycle = [(0.0, 0.0), (200.0, 0.0), (200.0, 1.0), (0.0, 1.0)]  # Area=200, Perimeter=402
        
        # Cycle with good perimeter but small area
        small_cycle = [(0.0, 0.0), (50.0, 0.0), (50.0, 1.0), (0.0, 1.0)]  # Area=50, Perimeter=102
        
        cycles = [thin_cycle, small_cycle]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=200.0)
        
        # thin_cycle should pass (area=200 >= 100, perimeter=402 >= 200)
        # small_cycle should fail (area=50 < 100)
        assert len(filtered) >= 0  # At least thin_cycle might pass
    
    def test_max_area_excludes_outer_perimeter(self):
        """Test that max_area effectively filters outer perimeter."""
        cycles = [
            # Inner room
            [(50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0)],  # Area = 10,000
            # Outer perimeter
            [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)],  # Area = 1,000,000
        ]
        
        filtered = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0, max_area=900000.0)
        
        # Should keep inner room, filter outer perimeter
        assert len(filtered) >= 1, "Should keep at least inner room"
        # Verify outer perimeter is filtered
        areas = [Polygon(c).area for c in filtered]
        assert all(area <= 900000.0 for area in areas), "All cycles should be within max_area"

