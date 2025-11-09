"""
Unit tests for PDF line filtering functionality.
"""

import pytest
import math
from src.pdf_parser import PDFParser, PDFLineSegment


class TestLineFiltering:
    """Test cases for line filtering."""
    
    def test_filter_by_thickness(self):
        """Test filtering by minimum thickness."""
        parser = PDFParser(min_line_thickness=2.0)
        
        lines = [
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=1.0, color=(0, 0, 0), page_number=0),  # Too thin
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0, 0, 0), page_number=0),  # Minimum
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=3.0, color=(0, 0, 0), page_number=0),  # Thick enough
        ]
        
        filtered = parser.filter_wall_lines(lines, min_thickness=2.0)
        
        assert len(filtered) == 2
        assert all(line.thickness >= 2.0 for line in filtered)
    
    def test_filter_by_max_thickness(self):
        """Test filtering by maximum thickness."""
        parser = PDFParser()
        
        lines = [
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=5.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=10.0, color=(0, 0, 0), page_number=0),  # Too thick
        ]
        
        filtered = parser.filter_wall_lines(lines, max_thickness=5.0)
        
        assert len(filtered) == 2
        assert all(line.thickness <= 5.0 for line in filtered)
    
    def test_filter_by_length(self):
        """Test filtering by minimum line length."""
        parser = PDFParser()
        
        lines = [
            PDFLineSegment(start=(0, 0), end=(5, 0), thickness=2.0, color=(0, 0, 0), page_number=0),  # Too short
            PDFLineSegment(start=(0, 0), end=(10, 0), thickness=2.0, color=(0, 0, 0), page_number=0),  # Minimum
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0, 0, 0), page_number=0),  # Long enough
        ]
        
        filtered = parser.filter_wall_lines(lines, min_length=10.0)
        
        assert len(filtered) == 2
        for line in filtered:
            length = math.sqrt((line.end[0] - line.start[0])**2 + (line.end[1] - line.start[1])**2)
            assert length >= 10.0
    
    def test_filter_by_color(self):
        """Test filtering by preferred colors."""
        parser = PDFParser()
        
        lines = [
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0, 0, 0), page_number=0),  # Black - match
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(1, 1, 1), page_number=0),  # White - no match
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0.1, 0.1, 0.1), page_number=0),  # Dark gray - match
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0.5, 0.5, 0.5), page_number=0),  # Gray - no match
        ]
        
        # Filter for black/dark colors
        filtered = parser.filter_wall_lines(
            lines, 
            preferred_colors=[(0, 0, 0), (0.1, 0.1, 0.1)],
            color_tolerance=0.2
        )
        
        assert len(filtered) == 2
        assert filtered[0].color == (0, 0, 0)
        assert filtered[1].color == (0.1, 0.1, 0.1)
    
    def test_filter_combines_criteria(self):
        """Test that filtering combines all criteria."""
        parser = PDFParser()
        
        lines = [
            # Too thin
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=1.0, color=(0, 0, 0), page_number=0),
            # Too short
            PDFLineSegment(start=(0, 0), end=(5, 0), thickness=2.0, color=(0, 0, 0), page_number=0),
            # Wrong color
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(1, 1, 1), page_number=0),
            # All criteria met
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        filtered = parser.filter_wall_lines(
            lines,
            min_thickness=2.0,
            min_length=10.0,
            preferred_colors=[(0, 0, 0)],
            color_tolerance=0.3
        )
        
        assert len(filtered) == 1
        assert filtered[0].thickness == 2.0
        assert filtered[0].color == (0, 0, 0)
    
    def test_filter_empty_list(self):
        """Test filtering empty list."""
        parser = PDFParser()
        filtered = parser.filter_wall_lines([])
        assert filtered == []
    
    def test_filter_no_preferred_colors(self):
        """Test filtering without color preferences (all colors allowed)."""
        parser = PDFParser()
        
        lines = [
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0, 0, 0), page_number=0),
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(1, 1, 1), page_number=0),
            PDFLineSegment(start=(0, 0), end=(100, 0), thickness=2.0, color=(0.5, 0.5, 0.5), page_number=0),
        ]
        
        # Pass empty list to skip color filtering
        filtered = parser.filter_wall_lines(lines, preferred_colors=[])
        
        # All should pass (only thickness and length filters apply)
        assert len(filtered) == 3
    
    def test_filter_diagonal_lines(self):
        """Test that diagonal lines are filtered correctly by length."""
        parser = PDFParser()
        
        # Diagonal line: sqrt(50^2 + 50^2) = ~70.7
        lines = [
            PDFLineSegment(start=(0, 0), end=(50, 50), thickness=2.0, color=(0, 0, 0), page_number=0),
        ]
        
        filtered = parser.filter_wall_lines(lines, min_length=70.0)
        assert len(filtered) == 1
        
        filtered = parser.filter_wall_lines(lines, min_length=80.0)
        assert len(filtered) == 0

