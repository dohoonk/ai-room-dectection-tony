"""
Validation module for image-extracted wall segments.

Reuses the existing SegmentValidator from pdf_validator.py since the validation
logic is the same for both PDF and image-extracted segments.
"""

from typing import List
from .pdf_validator import SegmentValidator, validate_pdf_segments
from .parser import WallSegment


def validate_image_segments(segments: List[WallSegment], 
                           strict: bool = False,
                           connectivity_tolerance: float = 5.0,
                           max_isolated_ratio: float = 0.9) -> dict:
    """
    Validate image-extracted wall segments.
    
    This function reuses the existing PDF validator since the validation
    logic is identical for both PDF and image-extracted segments.
    
    Args:
        segments: List of wall segments to validate
        strict: If True, raises ValidationError on any errors. If False, returns results.
        connectivity_tolerance: Tolerance for endpoint snapping (default 5.0 for images,
                               higher than default 1.0 due to coordinate precision)
        max_isolated_ratio: Maximum ratio of isolated segments (default 0.9 for images,
                            more lenient than default 0.5 due to extraction precision)
        
    Returns:
        Validation results dictionary (see SegmentValidator.validate_segments)
        
    Raises:
        ValidationError: If strict=True and validation fails
    """
    # Use the same validation logic as PDF segments
    # Images may have similar precision issues after normalization
    return validate_pdf_segments(
        segments,
        strict=strict,
        connectivity_tolerance=connectivity_tolerance,
        max_isolated_ratio=max_isolated_ratio
    )

