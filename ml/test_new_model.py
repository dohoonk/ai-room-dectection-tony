#!/usr/bin/env python3
"""
Quick test script for the newly trained SageMaker model.
"""

import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from src.ml_room_detector import MLRoomDetector
import cv2

def test_model(image_path: str, confidence: float = 0.05):
    """Test the model on a sample image."""
    print(f"🧪 Testing model on: {image_path}")
    print(f"📊 Confidence threshold: {confidence}")
    print()
    
    # Initialize detector (uses default model path)
    try:
        print("📦 Loading model...")
        detector = MLRoomDetector()
        print("✅ Model loaded!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Load image
    print(f"\n🖼️  Loading image: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image from: {image_path}")
        return
    
    img_height, img_width = image.shape[:2]
    print(f"✅ Image loaded: {img_width}x{img_height}")
    
    # Detect rooms
    print(f"\n🔍 Detecting rooms (confidence: {confidence})...")
    rooms = detector.detect_rooms(image, confidence_threshold=confidence)
    
    print(f"\n📊 Results:")
    print(f"   Detected {len(rooms)} rooms")
    
    if rooms:
        print(f"\n   Room details:")
        for i, room in enumerate(rooms):
            print(f"   Room {i+1}:")
            print(f"     - Confidence: {room['confidence']:.3f}")
            print(f"     - Polygon points: {len(room['polygon'])}")
            if len(room['polygon']) > 0:
                x_coords = [p[0] for p in room['polygon']]
                y_coords = [p[1] for p in room['polygon']]
                print(f"     - BBox: ({min(x_coords)}, {min(y_coords)}) to ({max(x_coords)}, {max(y_coords)})")
    else:
        print("\n   ⚠️  No rooms detected!")
        print("   💡 Try lowering confidence threshold (e.g., 0.01)")
    
    # Convert to bounding boxes
    print(f"\n🔄 Converting to bounding boxes...")
    converted = detector.convert_to_bounding_boxes(rooms, normalize=True)
    print(f"   Converted {len(converted)} rooms to bounding boxes")
    
    if converted:
        print(f"\n   Bounding boxes (normalized 0-1000):")
        for room in converted[:3]:  # Show first 3
            bbox = room['bounding_box']
            print(f"   {room['id']}: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the trained YOLOv8 model")
    parser.add_argument("--image", type=str, required=True, help="Path to test image")
    parser.add_argument("--confidence", type=float, default=0.05, help="Confidence threshold (default: 0.05)")
    
    args = parser.parse_args()
    
    test_model(args.image, args.confidence)

