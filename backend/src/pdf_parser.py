"""
PDF Vector Extraction Module

Extracts wall line segments from PDF blueprint files using PyMuPDF (fitz).
Handles vector graphics extraction, coordinate transformation, and line filtering.
"""

import fitz  # PyMuPDF
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import math


@dataclass
class PDFLineSegment:
    """Represents a line segment extracted from a PDF."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    thickness: float
    color: Tuple[float, float, float]  # RGB values (0-1)
    page_number: int


class PDFParser:
    """Parser for extracting vector graphics from PDF files."""
    
    def __init__(self, min_line_thickness: float = 2.0):
        """
        Initialize PDF parser.
        
        Args:
            min_line_thickness: Minimum line thickness to consider (in points)
        """
        self.min_line_thickness = min_line_thickness
    
    def open_pdf(self, pdf_path: str) -> fitz.Document:
        """
        Open a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PyMuPDF Document object
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF cannot be opened
        """
        try:
            doc = fitz.open(pdf_path)
            return doc
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise Exception(f"Error opening PDF: {str(e)}")
    
    def get_page_dimensions(self, page: fitz.Page) -> Tuple[float, float]:
        """
        Get page dimensions in points.
        
        Args:
            page: PyMuPDF Page object
            
        Returns:
            Tuple of (width, height) in points
        """
        rect = page.rect
        return (rect.width, rect.height)
    
    def extract_lines(self, page: fitz.Page, page_number: int = 0) -> List[PDFLineSegment]:
        """
        Extract line segments from a PDF page.
        
        PyMuPDF's get_drawings() returns a list of dictionaries with:
        - "items": List of path commands (tuples)
        - "width": Line thickness
        - "color": RGB color tuple (0-1 range)
        - "rect": Bounding rectangle
        
        Path commands are tuples like:
        - ("l", x1, y1, x2, y2): Line from (x1,y1) to (x2,y2)
        - ("m", x, y): Move to point (x, y)
        - ("c", x1, y1, x2, y2, x3, y3): Cubic Bezier curve
        
        Args:
            page: PyMuPDF Page object
            page_number: Page number (0-indexed)
            
        Returns:
            List of PDFLineSegment objects
        """
        lines = []
        
        # Get all drawings (vector paths) from the page
        drawings = page.get_drawings()
        
        for drawing in drawings:
            # Get line properties
            thickness = drawing.get("width", 1.0)
            color = drawing.get("color", (0.0, 0.0, 0.0))  # Default to black (RGB 0-1)
            
            # Filter by minimum thickness
            if thickness < self.min_line_thickness:
                continue
            
            # Extract line segments from drawing items
            items = drawing.get("items", [])
            current_point = None
            
            for item in items:
                if not item:
                    continue
                
                # Handle different path command types
                if item[0] == "l":  # Line command: ("l", x1, y1, x2, y2)
                    if len(item) == 5:
                        start = (float(item[1]), float(item[2]))
                        end = (float(item[3]), float(item[4]))
                        
                        # Only add if start and end are different
                        if start != end:
                            lines.append(PDFLineSegment(
                                start=start,
                                end=end,
                                thickness=thickness,
                                color=color,
                                page_number=page_number
                            ))
                            current_point = end
                
                elif item[0] == "m":  # Move command: ("m", x, y)
                    if len(item) == 3:
                        current_point = (float(item[1]), float(item[2]))
                
                elif item[0] == "c":  # Cubic Bezier curve: ("c", x1, y1, x2, y2, x3, y3)
                    # For curves, we'll approximate with a line from start to end
                    # This is a simplification - could be improved to extract more points
                    if len(item) == 7 and current_point:
                        start = current_point
                        end = (float(item[5]), float(item[6]))  # End point of curve
                        
                        if start != end:
                            lines.append(PDFLineSegment(
                                start=start,
                                end=end,
                                thickness=thickness,
                                color=color,
                                page_number=page_number
                            ))
                            current_point = end
        
        return lines
    
    def extract_all_lines(self, pdf_path: str) -> List[PDFLineSegment]:
        """
        Extract all line segments from all pages of a PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PDFLineSegment objects from all pages
        """
        doc = self.open_pdf(pdf_path)
        all_lines = []
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                lines = self.extract_lines(page, page_num)
                all_lines.extend(lines)
        finally:
            doc.close()
        
        return all_lines
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get basic information about a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        doc = self.open_pdf(pdf_path)
        
        try:
            info = {
                "page_count": len(doc),
                "pages": []
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                width, height = self.get_page_dimensions(page)
                info["pages"].append({
                    "page_number": page_num,
                    "width": width,
                    "height": height
                })
            
            return info
        finally:
            doc.close()


def test_pdf_parser():
    """Test function to verify PDF parser setup."""
    parser = PDFParser(min_line_thickness=2.0)
    
    # Test that we can import and instantiate
    assert parser is not None
    assert parser.min_line_thickness == 2.0
    
    print("✅ PDF Parser setup successful!")
    print(f"   Min line thickness: {parser.min_line_thickness} points")
    
    return parser


if __name__ == "__main__":
    # Run test
    test_pdf_parser()

