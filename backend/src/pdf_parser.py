"""
PDF Vector Extraction Module

Extracts wall line segments from PDF blueprint files using PyMuPDF (fitz).
Handles vector graphics extraction, coordinate transformation, and line filtering.
"""

import fitz  # PyMuPDF
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import math
import os


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
        except (FileNotFoundError, fitz.FileNotFoundError) as e:
            # PyMuPDF raises fitz.FileNotFoundError which is a subclass
            raise FileNotFoundError(f"PDF file not found: {pdf_path}") from e
        except Exception as e:
            raise Exception(f"Error opening PDF: {str(e)}") from e
    
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


    def transform_coordinates(self, pdf_lines: List[PDFLineSegment], 
                            pdf_info: Optional[Dict[str, Any]] = None,
                            target_range: Tuple[int, int] = (0, 1000)) -> List[PDFLineSegment]:
        """
        Transform PDF coordinates to normalized 0-1000 range.
        
        This function:
        1. Finds the bounding box of all extracted lines
        2. Calculates scale factor to fit in target range (preserving aspect ratio)
        3. Transforms all coordinates to normalized range
        
        Args:
            pdf_lines: List of PDFLineSegment objects with PDF coordinates
            pdf_info: Optional PDF info dictionary (for page dimensions)
            target_range: Target coordinate range (min, max), default (0, 1000)
            
        Returns:
            List of PDFLineSegment objects with normalized coordinates
        """
        if not pdf_lines:
            return []
        
        # Find bounding box of all lines
        all_x = []
        all_y = []
        
        for line in pdf_lines:
            all_x.extend([line.start[0], line.end[0]])
            all_y.extend([line.start[1], line.end[1]])
        
        if not all_x or not all_y:
            return pdf_lines
        
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)
        
        # Calculate dimensions
        width = max_x - min_x
        height = max_y - min_y
        
        if width == 0 or height == 0:
            # Degenerate case - return lines as-is
            return pdf_lines
        
        # Calculate scale factor to fit in target range (preserve aspect ratio)
        min_val, max_val = target_range
        target_size = max_val - min_val
        
        scale_x = target_size / width if width > 0 else 1.0
        scale_y = target_size / height if height > 0 else 1.0
        scale = min(scale_x, scale_y)  # Preserve aspect ratio
        
        # Calculate offset to center in target range
        scaled_width = width * scale
        scaled_height = height * scale
        
        offset_x = min_val - (min_x * scale) + (target_size - scaled_width) / 2
        offset_y = min_val - (min_y * scale) + (target_size - scaled_height) / 2
        
        # Transform all lines
        normalized_lines = []
        for line in pdf_lines:
            # Transform start and end coordinates
            normalized_start = (
                line.start[0] * scale + offset_x,
                line.start[1] * scale + offset_y
            )
            normalized_end = (
                line.end[0] * scale + offset_y,
                line.end[1] * scale + offset_y
            )
            
            # Clamp to target range (safety check)
            normalized_start = (
                max(min_val, min(max_val, normalized_start[0])),
                max(min_val, min(max_val, normalized_start[1]))
            )
            normalized_end = (
                max(min_val, min(max_val, normalized_end[0])),
                max(min_val, min(max_val, normalized_end[1]))
            )
            
            normalized_lines.append(PDFLineSegment(
                start=normalized_start,
                end=normalized_end,
                thickness=line.thickness,
                color=line.color,
                page_number=line.page_number
            ))
        
        return normalized_lines
    
    def convert_to_wall_segments(self, pdf_lines: List[PDFLineSegment], 
                                normalize: bool = True) -> List[Dict[str, Any]]:
        """
        Convert PDFLineSegment objects to wall segment format.
        
        This converts the extracted PDF lines to a format compatible with
        our existing wall segment parser. Optionally normalizes coordinates.
        
        Args:
            pdf_lines: List of PDFLineSegment objects (normalized if normalize=True)
            normalize: If True, assumes coordinates are already normalized to 0-1000
            
        Returns:
            List of dictionaries in wall segment format
        """
        wall_segments = []
        
        for line in pdf_lines:
            # Validate coordinates are in 0-1000 range if normalized
            if normalize:
                for coord in [line.start[0], line.start[1], line.end[0], line.end[1]]:
                    if not (0 <= coord <= 1000):
                        raise ValueError(
                            f"Coordinate {coord} is outside 0-1000 range. "
                            "Ensure coordinates are normalized before conversion."
                        )
            
            wall_segments.append({
                "type": "line",
                "start": [line.start[0], line.start[1]],
                "end": [line.end[0], line.end[1]],
                "is_load_bearing": line.thickness >= 3.0,  # Heuristic: thicker lines are load-bearing
                "pdf_metadata": {
                    "thickness": line.thickness,
                    "color": line.color,
                    "page_number": line.page_number
                }
            })
        
        return wall_segments


def test_pdf_parser():
    """Test function to verify PDF parser setup."""
    parser = PDFParser(min_line_thickness=2.0)
    
    # Test that we can import and instantiate
    assert parser is not None
    assert parser.min_line_thickness == 2.0
    
    print("✅ PDF Parser setup successful!")
    print(f"   Min line thickness: {parser.min_line_thickness} points")
    
    return parser


def test_extraction_with_pdf(pdf_path: str):
    """
    Test PDF extraction with an actual PDF file.
    
    Args:
        pdf_path: Path to PDF file to test
    """
    if not os.path.exists(pdf_path):
        print(f"⚠️  PDF file not found: {pdf_path}")
        print("   Skipping extraction test. Provide a PDF file to test extraction.")
        return
    
    parser = PDFParser(min_line_thickness=2.0)
    
    try:
        # Get PDF info
        info = parser.get_pdf_info(pdf_path)
        print(f"\n📄 PDF Info:")
        print(f"   Pages: {info['page_count']}")
        for page in info['pages']:
            print(f"   Page {page['page_number']}: {page['width']:.1f} x {page['height']:.1f} points")
        
        # Extract lines
        lines = parser.extract_all_lines(pdf_path)
        print(f"\n📏 Extracted Lines:")
        print(f"   Total lines: {len(lines)}")
        
        if lines:
            # Group by page
            by_page = {}
            for line in lines:
                page = line.page_number
                if page not in by_page:
                    by_page[page] = []
                by_page[page].append(line)
            
            for page_num, page_lines in sorted(by_page.items()):
                print(f"   Page {page_num}: {len(page_lines)} lines")
            
            # Show sample lines
            print(f"\n   Sample lines (first 5):")
            for i, line in enumerate(lines[:5]):
                print(f"     {i+1}. ({line.start[0]:.1f}, {line.start[1]:.1f}) -> ({line.end[0]:.1f}, {line.end[1]:.1f}), thickness: {line.thickness:.1f}")
        
        # Transform coordinates to 0-1000 range
        print(f"\n🔄 Coordinate Transformation:")
        normalized_lines = parser.transform_coordinates(lines, pdf_info=info)
        print(f"   Normalized {len(normalized_lines)} lines to 0-1000 range")
        
        if normalized_lines:
            # Show sample normalized coordinates
            print(f"   Sample normalized coordinates (first 3):")
            for i, line in enumerate(normalized_lines[:3]):
                print(f"     {i+1}. ({line.start[0]:.1f}, {line.start[1]:.1f}) -> ({line.end[0]:.1f}, {line.end[1]:.1f})")
        
        # Convert to wall segments (with normalized coordinates)
        wall_segments = parser.convert_to_wall_segments(normalized_lines, normalize=True)
        print(f"\n🏗️  Wall Segments (Normalized):")
        print(f"   Total segments: {len(wall_segments)}")
        
        if wall_segments:
            load_bearing = sum(1 for seg in wall_segments if seg['is_load_bearing'])
            print(f"   Load-bearing: {load_bearing}")
            print(f"   Regular: {len(wall_segments) - load_bearing}")
        
        print("\n✅ PDF extraction and transformation test completed!")
        
    except Exception as e:
        print(f"\n❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    import os
    
    # Run basic test
    test_pdf_parser()
    
    # If PDF path provided, test extraction
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_extraction_with_pdf(pdf_path)
    else:
        print("\n💡 To test extraction with a PDF file:")
        print("   python -m src.pdf_parser <path_to_pdf>")

