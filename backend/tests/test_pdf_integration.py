"""
Integration test for PDF processing pipeline using sample_pdf.pdf.

Tests the complete flow from PDF extraction to room detection.
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_parser import PDFParser
from src.pdf_validator import validate_pdf_segments
from src.room_detector import detect_rooms
from src.parser import WallSegment


# Get the path to sample_pdf.pdf (should be in project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SAMPLE_PDF_PATH = PROJECT_ROOT / "sample_pdf.pdf"


@pytest.fixture
def sample_pdf_path():
    """Return path to sample_pdf.pdf if it exists."""
    if not SAMPLE_PDF_PATH.exists():
        pytest.skip(f"sample_pdf.pdf not found at {SAMPLE_PDF_PATH}")
    return str(SAMPLE_PDF_PATH)


@pytest.fixture
def pdf_parser():
    """Create a PDFParser instance for testing."""
    return PDFParser(min_line_thickness=0.5)


class TestPDFIntegration:
    """Integration tests for complete PDF processing pipeline."""
    
    def test_pdf_file_exists(self, sample_pdf_path):
        """Test that sample_pdf.pdf exists."""
        assert os.path.exists(sample_pdf_path), f"PDF file not found: {sample_pdf_path}"
    
    def test_pdf_extraction(self, sample_pdf_path, pdf_parser):
        """Test that we can extract lines from the PDF."""
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        doc.close()
        
        assert len(lines) > 0, "Should extract at least some lines from PDF"
        assert len(lines) > 100, f"Expected more than 100 lines, got {len(lines)}"
        
        # Verify line structure
        for line in lines[:5]:  # Check first 5 lines
            assert hasattr(line, 'start'), "Line should have start attribute"
            assert hasattr(line, 'end'), "Line should have end attribute"
            assert len(line.start) == 2, "Start should be (x, y) tuple"
            assert len(line.end) == 2, "End should be (x, y) tuple"
    
    def test_pdf_coordinate_transformation(self, sample_pdf_path, pdf_parser):
        """Test coordinate transformation to normalized 0-1000 range."""
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        doc.close()
        
        normalized = pdf_parser.transform_coordinates(lines)
        
        assert len(normalized) == len(lines), "Should preserve line count"
        
        # Check that coordinates are in 0-1000 range
        for line in normalized:
            assert 0 <= line.start[0] <= 1000, f"Start x should be 0-1000, got {line.start[0]}"
            assert 0 <= line.start[1] <= 1000, f"Start y should be 0-1000, got {line.start[1]}"
            assert 0 <= line.end[0] <= 1000, f"End x should be 0-1000, got {line.end[0]}"
            assert 0 <= line.end[1] <= 1000, f"End y should be 0-1000, got {line.end[1]}"
    
    def test_pdf_line_filtering(self, sample_pdf_path, pdf_parser):
        """Test filtering of wall lines."""
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        normalized = pdf_parser.transform_coordinates(lines)
        doc.close()
        
        filtered = pdf_parser.filter_wall_lines(
            normalized,
            min_thickness=0.5,
            min_length=5.0
        )
        
        assert len(filtered) > 0, "Should have at least some filtered lines"
        assert len(filtered) <= len(normalized), "Filtered should be <= normalized"
        
        # Verify filtered lines meet criteria
        for line in filtered:
            assert line.thickness >= 0.5, f"Thickness should be >= 0.5, got {line.thickness}"
            length = ((line.end[0] - line.start[0])**2 + (line.end[1] - line.start[1])**2)**0.5
            assert length >= 5.0, f"Length should be >= 5.0, got {length}"
    
    def test_pdf_segment_conversion(self, sample_pdf_path, pdf_parser):
        """Test conversion to wall segments."""
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        normalized = pdf_parser.transform_coordinates(lines)
        filtered = pdf_parser.filter_wall_lines(normalized, min_thickness=0.5, min_length=5.0)
        doc.close()
        
        wall_segments_dict = pdf_parser.convert_to_wall_segments(filtered, normalize=True)
        
        assert len(wall_segments_dict) > 0, "Should have at least some wall segments"
        
        # Verify segment structure
        for seg in wall_segments_dict[:5]:  # Check first 5
            assert 'start' in seg, "Segment should have 'start'"
            assert 'end' in seg, "Segment should have 'end'"
            assert len(seg['start']) == 2, "Start should be [x, y]"
            assert len(seg['end']) == 2, "End should be [x, y]"
            assert 'is_load_bearing' in seg, "Segment should have 'is_load_bearing'"
    
    def test_pdf_segment_validation(self, sample_pdf_path, pdf_parser):
        """Test validation of PDF-extracted segments."""
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        normalized = pdf_parser.transform_coordinates(lines)
        filtered = pdf_parser.filter_wall_lines(normalized, min_thickness=0.5, min_length=5.0)
        wall_segments_dict = pdf_parser.convert_to_wall_segments(filtered, normalize=True)
        doc.close()
        
        # Convert to WallSegment objects
        wall_segments = [
            WallSegment(
                start=(seg['start'][0], seg['start'][1]),
                end=(seg['end'][0], seg['end'][1]),
                is_load_bearing=seg.get('is_load_bearing', False)
            )
            for seg in wall_segments_dict
        ]
        
        # Validate with lenient settings for PDFs
        result = validate_pdf_segments(
            wall_segments,
            strict=False,
            connectivity_tolerance=5.0,
            max_isolated_ratio=0.9
        )
        
        assert result['valid'], f"Validation should pass. Errors: {result.get('errors', [])}"
        assert len(result['errors']) == 0, f"Should have no errors: {result['errors']}"
        assert result['stats']['count'] > 0, "Should have segments"
    
    def test_pdf_room_detection(self, sample_pdf_path, pdf_parser):
        """Test complete pipeline: PDF -> Room Detection."""
        # Extract and process PDF
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        normalized = pdf_parser.transform_coordinates(lines)
        filtered = pdf_parser.filter_wall_lines(normalized, min_thickness=0.5, min_length=5.0)
        wall_segments_dict = pdf_parser.convert_to_wall_segments(filtered, normalize=True)
        doc.close()
        
        # Create temporary JSON file for detect_rooms
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            walls_data = [
                {
                    "type": "line",
                    "start": [seg['start'][0], seg['start'][1]],
                    "end": [seg['end'][0], seg['end'][1]],
                    "is_load_bearing": seg.get('is_load_bearing', False)
                }
                for seg in wall_segments_dict
            ]
            json.dump(walls_data, f)
            temp_json_path = f.name
        
        try:
            # Detect rooms with higher tolerance for PDFs
            rooms = detect_rooms(temp_json_path, tolerance=5.0)
            
            # Verify rooms were detected
            assert len(rooms) > 0, f"Should detect at least 1 room, got {len(rooms)}"
            assert len(rooms) >= 10, f"Expected at least 10 rooms from sample PDF, got {len(rooms)}"
            
            # Verify room structure
            for room in rooms:
                assert 'id' in room, "Room should have 'id'"
                assert 'bounding_box' in room, "Room should have 'bounding_box'"
                assert 'name_hint' in room, "Room should have 'name_hint'"
                
                bbox = room['bounding_box']
                assert len(bbox) == 4, "Bounding box should be [x_min, y_min, x_max, y_max]"
                assert bbox[0] < bbox[2], "x_min should be < x_max"
                assert bbox[1] < bbox[3], "y_min should be < y_max"
                
                # Verify coordinates are in 0-1000 range
                for coord in bbox:
                    assert 0 <= coord <= 1000, f"Coordinate should be 0-1000, got {coord}"
        
        finally:
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)
    
    def test_pdf_processing_statistics(self, sample_pdf_path, pdf_parser):
        """Test that we get reasonable statistics from PDF processing."""
        doc = pdf_parser.open_pdf(sample_pdf_path)
        page = doc[0]
        lines = pdf_parser.extract_lines(page, page_number=0)
        normalized = pdf_parser.transform_coordinates(lines)
        filtered = pdf_parser.filter_wall_lines(normalized, min_thickness=0.5, min_length=5.0)
        wall_segments_dict = pdf_parser.convert_to_wall_segments(filtered, normalize=True)
        doc.close()
        
        # Print statistics for debugging
        print(f"\n📊 PDF Processing Statistics:")
        print(f"   Raw lines extracted: {len(lines)}")
        print(f"   Lines after normalization: {len(normalized)}")
        print(f"   Lines after filtering: {len(filtered)}")
        print(f"   Wall segments: {len(wall_segments_dict)}")
        
        # Verify reasonable numbers
        assert len(lines) > 100, f"Should extract > 100 lines, got {len(lines)}"
        assert len(filtered) > 50, f"Should have > 50 filtered lines, got {len(filtered)}"
        assert len(wall_segments_dict) > 50, f"Should have > 50 wall segments, got {len(wall_segments_dict)}"

