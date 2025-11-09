"""
Unit tests for PDF coordinate transformation.
"""

import pytest
from src.pdf_parser import PDFParser, PDFLineSegment


class TestCoordinateTransformation:
    """Test cases for coordinate transformation."""
    
    def test_transform_simple_lines(self):
        """Test transformation of simple lines."""
        parser = PDFParser()
        
        # Create lines in a 100x100 PDF coordinate system
        pdf_lines = [
            PDFLineSegment(start=(0.0, 0.0), end=(100.0, 0.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(100.0, 0.0), end=(100.0, 100.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(100.0, 100.0), end=(0.0, 100.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(0.0, 100.0), end=(0.0, 0.0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        normalized = parser.transform_coordinates(pdf_lines, target_range=(0, 1000))
        
        assert len(normalized) == 4
        # All coordinates should be in 0-1000 range
        for line in normalized:
            assert 0 <= line.start[0] <= 1000
            assert 0 <= line.start[1] <= 1000
            assert 0 <= line.end[0] <= 1000
            assert 0 <= line.end[1] <= 1000
    
    def test_transform_preserves_aspect_ratio(self):
        """Test that transformation preserves aspect ratio."""
        parser = PDFParser()
        
        # Create a rectangle (200 wide, 100 tall) - aspect ratio 2:1
        pdf_lines = [
            PDFLineSegment(start=(0.0, 0.0), end=(200.0, 0.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(200.0, 0.0), end=(200.0, 100.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(200.0, 100.0), end=(0.0, 100.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(0.0, 100.0), end=(0.0, 0.0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        normalized = parser.transform_coordinates(pdf_lines, target_range=(0, 1000))
        
        # Find bounding box of normalized lines
        all_x = []
        all_y = []
        for line in normalized:
            all_x.extend([line.start[0], line.end[0]])
            all_y.extend([line.start[1], line.end[1]])
        
        width = max(all_x) - min(all_x)
        height = max(all_y) - min(all_y)
        
        # Aspect ratio should be preserved (approximately 2:1)
        aspect_ratio = width / height if height > 0 else 0
        assert abs(aspect_ratio - 2.0) < 0.1, f"Aspect ratio should be ~2:1, got {aspect_ratio}"
    
    def test_transform_empty_list(self):
        """Test transformation of empty list."""
        parser = PDFParser()
        normalized = parser.transform_coordinates([], target_range=(0, 1000))
        assert normalized == []
    
    def test_transform_single_point(self):
        """Test transformation with degenerate case (zero width/height)."""
        parser = PDFParser()
        
        # All lines at same point
        pdf_lines = [
            PDFLineSegment(start=(50.0, 50.0), end=(50.0, 50.0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        normalized = parser.transform_coordinates(pdf_lines, target_range=(0, 1000))
        
        # Should return lines as-is for degenerate case
        assert len(normalized) == 1
    
    def test_transform_large_coordinates(self):
        """Test transformation of large coordinates."""
        parser = PDFParser()
        
        # Lines in a 2000x1500 coordinate system
        pdf_lines = [
            PDFLineSegment(start=(0.0, 0.0), end=(2000.0, 0.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(2000.0, 0.0), end=(2000.0, 1500.0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        normalized = parser.transform_coordinates(pdf_lines, target_range=(0, 1000))
        
        # All coordinates should be in 0-1000 range
        for line in normalized:
            assert 0 <= line.start[0] <= 1000
            assert 0 <= line.start[1] <= 1000
            assert 0 <= line.end[0] <= 1000
            assert 0 <= line.end[1] <= 1000
    
    def test_transform_small_coordinates(self):
        """Test transformation of small coordinates."""
        parser = PDFParser()
        
        # Lines in a 10x10 coordinate system
        pdf_lines = [
            PDFLineSegment(start=(0.0, 0.0), end=(10.0, 0.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(10.0, 0.0), end=(10.0, 10.0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        normalized = parser.transform_coordinates(pdf_lines, target_range=(0, 1000))
        
        # Should be scaled up to fit in 0-1000 range
        for line in normalized:
            assert 0 <= line.start[0] <= 1000
            assert 0 <= line.start[1] <= 1000
            assert 0 <= line.end[0] <= 1000
            assert 0 <= line.end[1] <= 1000


class TestConvertToWallSegments:
    """Test cases for converting to wall segment format."""
    
    def test_convert_normalized_lines(self):
        """Test conversion of normalized lines."""
        parser = PDFParser()
        
        normalized_lines = [
            PDFLineSegment(start=(100.0, 100.0), end=(500.0, 100.0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(500.0, 100.0), end=(500.0, 400.0), thickness=4.0, color=(0, 0, 0), page_number=0),
        ]
        
        wall_segments = parser.convert_to_wall_segments(normalized_lines, normalize=True)
        
        assert len(wall_segments) == 2
        assert wall_segments[0]["type"] == "line"
        assert wall_segments[0]["start"] == [100.0, 100.0]
        assert wall_segments[0]["end"] == [500.0, 100.0]
        assert wall_segments[0]["is_load_bearing"] == False  # thickness 2.0 < 3.0
        assert wall_segments[1]["is_load_bearing"] == True  # thickness 4.0 >= 3.0
    
    def test_convert_with_invalid_coordinates(self):
        """Test conversion fails with coordinates outside 0-1000 range."""
        parser = PDFParser()
        
        # Line with coordinates outside 0-1000 range
        invalid_lines = [
            PDFLineSegment(start=(1500.0, 100.0), end=(2000.0, 100.0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        with pytest.raises(ValueError, match="outside 0-1000 range"):
            parser.convert_to_wall_segments(invalid_lines, normalize=True)
    
    def test_convert_preserves_metadata(self):
        """Test that conversion preserves PDF metadata."""
        parser = PDFParser()
        
        normalized_lines = [
            PDFLineSegment(start=(100.0, 100.0), end=(200.0, 100.0), thickness=2.5, color=(0.5, 0.5, 0.5), page_number=1),
        ]
        
        wall_segments = parser.convert_to_wall_segments(normalized_lines, normalize=True)
        
        assert len(wall_segments) == 1
        assert "pdf_metadata" in wall_segments[0]
        assert wall_segments[0]["pdf_metadata"]["thickness"] == 2.5
        assert wall_segments[0]["pdf_metadata"]["color"] == (0.5, 0.5, 0.5)
        assert wall_segments[0]["pdf_metadata"]["page_number"] == 1

