"""
Unit tests for PDF parser module.
"""

import pytest
import os
import tempfile
from pathlib import Path
from src.pdf_parser import PDFParser, PDFLineSegment


def test_pdf_parser_initialization():
    """Test PDFParser can be instantiated."""
    parser = PDFParser(min_line_thickness=2.0)
    assert parser is not None
    assert parser.min_line_thickness == 2.0


def test_pdf_parser_default_thickness():
    """Test PDFParser uses default thickness."""
    parser = PDFParser()
    assert parser.min_line_thickness == 2.0


def test_pdf_parser_custom_thickness():
    """Test PDFParser accepts custom thickness."""
    parser = PDFParser(min_line_thickness=5.0)
    assert parser.min_line_thickness == 5.0


def test_open_nonexistent_pdf():
    """Test opening a non-existent PDF raises FileNotFoundError."""
    parser = PDFParser()
    with pytest.raises(FileNotFoundError):
        parser.open_pdf("nonexistent.pdf")


def test_pdf_line_segment_creation():
    """Test PDFLineSegment can be created."""
    segment = PDFLineSegment(
        start=(0.0, 0.0),
        end=(100.0, 100.0),
        thickness=2.0,
        color=(0.0, 0.0, 0.0),
        page_number=0
    )
    assert segment.start == (0.0, 0.0)
    assert segment.end == (100.0, 100.0)
    assert segment.thickness == 2.0
    assert segment.color == (0.0, 0.0, 0.0)
    assert segment.page_number == 0


# Note: Tests that require actual PDF files would need sample PDFs
# For now, we test the structure and error handling
# Integration tests with real PDFs will be added when we have sample files

