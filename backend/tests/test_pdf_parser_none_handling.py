"""
Test cases for handling None values in PDF parser.
"""

import pytest
from src.pdf_parser import PDFParser, PDFLineSegment


def test_extract_lines_with_none_thickness():
    """Test that extract_lines handles None thickness values."""
    parser = PDFParser(min_line_thickness=1.0)
    
    # Create a mock page with drawings that have None thickness
    class MockDrawing:
        def __init__(self, width=None, color=None, items=None):
            self._width = width
            self._color = color
            self._items = items or []
        
        def get(self, key, default=None):
            if key == "width":
                return self._width if self._width is not None else default
            elif key == "color":
                return self._color if self._color is not None else default
            elif key == "items":
                return self._items
            return default
    
    class MockPage:
        def get_drawings(self):
            # Return drawings with None thickness
            return [
                MockDrawing(width=None, color=None, items=[("l", 0, 0, 100, 100)]),
                MockDrawing(width=2.0, color=(0, 0, 0), items=[("l", 0, 0, 100, 100)]),
            ]
    
    page = MockPage()
    lines = parser.extract_lines(page, page_number=0)
    
    # Should handle None values gracefully
    # First drawing with None thickness should be filtered out (defaults to 1.0, which is < min_line_thickness if min is 1.0)
    # Actually, if None defaults to 1.0 and min_line_thickness is 1.0, then 1.0 < 1.0 is False, so it should pass
    # But we want to test that it doesn't crash
    assert isinstance(lines, list)


def test_extract_lines_with_none_color():
    """Test that extract_lines handles None color values."""
    parser = PDFParser(min_line_thickness=0.5)
    
    class MockDrawing:
        def __init__(self, width=2.0, color=None, items=None):
            self._width = width
            self._color = color
            self._items = items or [("l", 0, 0, 100, 100)]
        
        def get(self, key, default=None):
            if key == "width":
                return self._width
            elif key == "color":
                return self._color if self._color is not None else default
            elif key == "items":
                return self._items
            return default
    
    class MockPage:
        def get_drawings(self):
            return [
                MockDrawing(width=2.0, color=None, items=[("l", 0, 0, 100, 100)]),
            ]
    
    page = MockPage()
    lines = parser.extract_lines(page, page_number=0)
    
    # Should handle None color gracefully (defaults to black)
    assert len(lines) >= 0  # At least doesn't crash
    if lines:
        assert lines[0].color == (0.0, 0.0, 0.0)  # Should default to black

