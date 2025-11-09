#!/usr/bin/env python3
"""
Add room type labels using OCR (Optical Character Recognition).

WHAT THIS DOES:
1. Takes room polygons from YOLOv8 predictions
2. Extracts text from each room region using OCR
3. Identifies room type labels (Kitchen, Bedroom, etc.)
4. Adds labels to room data

APPROACH:
- Extract text from each room polygon region
- Match text to known room types
- Assign room type to each room

REQUIREMENTS:
- pytesseract (Tesseract OCR)
- OR AWS Textract (if using AWS)
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import json
import re

# Try to import OCR libraries
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  Warning: pytesseract not installed. Install with: pip install pytesseract")

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Common room type keywords
ROOM_KEYWORDS = {
    'kitchen': ['kitchen', 'kit', 'k'],
    'bedroom': ['bedroom', 'bed', 'br', 'master bedroom', 'mb'],
    'bathroom': ['bathroom', 'bath', 'wc', 'toilet', 'powder room'],
    'living room': ['living room', 'living', 'lounge', 'family room', 'lr'],
    'dining room': ['dining room', 'dining', 'dr'],
    'office': ['office', 'study', 'den'],
    'closet': ['closet', 'wardrobe'],
    'hallway': ['hallway', 'hall', 'corridor'],
    'garage': ['garage', 'gar'],
    'laundry': ['laundry', 'laundry room'],
    'pantry': ['pantry'],
    'foyer': ['foyer', 'entry', 'entrance'],
    'basement': ['basement'],
    'attic': ['attic'],
}

def extract_text_from_region(
    image: np.ndarray,
    polygon: List[tuple],
    method: str = 'tesseract'
) -> str:
    """
    Extract text from a specific region of the image.
    
    Args:
        image: Full floor plan image
        polygon: List of (x, y) coordinates defining room region
        method: 'tesseract' or 'aws_textract'
    
    Returns:
        Extracted text string
    """
    # Create mask for this room region
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    polygon_array = np.array(polygon, dtype=np.int32)
    cv2.fillPoly(mask, [polygon_array], 255)
    
    # Extract region (crop to bounding box for efficiency)
    x_coords = [p[0] for p in polygon]
    y_coords = [p[1] for p in polygon]
    x_min, x_max = max(0, min(x_coords)), min(image.shape[1], max(x_coords))
    y_min, y_max = max(0, min(y_coords)), min(image.shape[0], max(y_coords))
    
    # Crop region
    region = image[y_min:y_max, x_min:x_max]
    region_mask = mask[y_min:y_max, x_min:x_max]
    
    # Apply mask (only process room region)
    region_masked = cv2.bitwise_and(region, region, mask=region_mask)
    
    # Convert to grayscale for OCR
    if len(region_masked.shape) == 3:
        gray = cv2.cvtColor(region_masked, cv2.COLOR_BGR2GRAY)
    else:
        gray = region_masked
    
    # Enhance contrast for better OCR
    gray = cv2.convertScaleAbs(gray, alpha=2.0, beta=30)
    
    # Extract text based on method
    if method == 'tesseract' and TESSERACT_AVAILABLE:
        # Use Tesseract OCR
        text = pytesseract.image_to_string(
            gray,
            config='--psm 8'  # Single word mode
        )
        return text.strip()
    
    elif method == 'aws_textract' and AWS_AVAILABLE:
        # Use AWS Textract
        # Note: This requires saving image temporarily or using bytes
        # For now, we'll use a simplified approach
        # In production, you'd upload to S3 and call Textract API
        print("⚠️  AWS Textract integration not fully implemented")
        return ""
    
    else:
        print(f"⚠️  OCR method '{method}' not available")
        return ""

def identify_room_type(text: str) -> Optional[str]:
    """
    Identify room type from extracted text.
    
    Args:
        text: Extracted text from OCR
    
    Returns:
        Room type name or None if not identified
    """
    if not text:
        return None
    
    text_lower = text.lower().strip()
    
    # Try to match against known room types
    for room_type, keywords in ROOM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return room_type
    
    return None

def add_labels_to_rooms(
    image_path: str,
    rooms: List[Dict[str, Any]],
    ocr_method: str = 'tesseract',
    confidence_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Add room type labels to room polygons using OCR.
    
    Args:
        image_path: Path to floor plan image
        rooms: List of room dictionaries (from extract_polygons.py)
        ocr_method: 'tesseract' or 'aws_textract'
        confidence_threshold: Minimum confidence to assign label
    
    Returns:
        Updated rooms list with 'room_type' field added
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    print(f"🔍 Processing {len(rooms)} rooms with OCR...")
    
    labeled_rooms = []
    
    for i, room in enumerate(rooms):
        polygon = room['polygon']
        
        # Extract text from room region
        text = extract_text_from_region(image, polygon, method=ocr_method)
        
        # Identify room type
        room_type = identify_room_type(text)
        
        # Create updated room dictionary
        updated_room = room.copy()
        updated_room['ocr_text'] = text
        updated_room['room_type'] = room_type if room_type else 'unknown'
        
        if room_type:
            print(f"   Room {i}: '{text}' → {room_type}")
        else:
            print(f"   Room {i}: '{text}' → (not identified)")
        
        labeled_rooms.append(updated_room)
    
    return labeled_rooms

def main():
    parser = argparse.ArgumentParser(
        description='Add room type labels using OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Using Tesseract OCR
  python ml/scripts/add_ocr_labels.py \\
    --input ml/results/results.json \\
    --image path/to/floorplan.png \\
    --output ml/results/labeled_results.json \\
    --method tesseract

  # Using AWS Textract (requires AWS credentials)
  python ml/scripts/add_ocr_labels.py \\
    --input ml/results/results.json \\
    --image path/to/floorplan.png \\
    --output ml/results/labeled_results.json \\
    --method aws_textract

Note: For Tesseract, you need to install Tesseract OCR separately:
  Mac: brew install tesseract
  Linux: sudo apt-get install tesseract-ocr
  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input JSON file with room polygons (from extract_polygons.py)'
    )
    
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Path to floor plan image'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='labeled_results.json',
        help='Output JSON file path (default: labeled_results.json)'
    )
    
    parser.add_argument(
        '--method',
        type=str,
        choices=['tesseract', 'aws_textract'],
        default='tesseract',
        help='OCR method to use (default: tesseract)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        return
    
    if not Path(args.image).exists():
        print(f"❌ Error: Image file not found: {args.image}")
        return
    
    # Check OCR availability
    if args.method == 'tesseract' and not TESSERACT_AVAILABLE:
        print("❌ Error: pytesseract not installed")
        print("   Install with: pip install pytesseract")
        print("   Also install Tesseract OCR system package")
        return
    
    # Load input data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    rooms = data.get('rooms', [])
    
    if not rooms:
        print("⚠️  Warning: No rooms found in input file")
        return
    
    # Add labels
    labeled_rooms = add_labels_to_rooms(
        args.image,
        rooms,
        ocr_method=args.method
    )
    
    # Save results
    output_data = {
        "image_path": args.image,
        "num_rooms": len(labeled_rooms),
        "rooms": labeled_rooms
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Print summary
    room_types = {}
    for room in labeled_rooms:
        room_type = room.get('room_type', 'unknown')
        room_types[room_type] = room_types.get(room_type, 0) + 1
    
    print(f"\n✅ Done!")
    print(f"   Processed {len(labeled_rooms)} rooms")
    print(f"   Room types found:")
    for room_type, count in sorted(room_types.items()):
        print(f"     - {room_type}: {count}")
    print(f"   Results saved to: {args.output}")

if __name__ == '__main__':
    main()

