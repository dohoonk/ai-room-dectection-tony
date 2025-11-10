#!/usr/bin/env python3
"""
Complete test script for the fine-tuned SageMaker model.
Run this script to test room detection on floor plan images.
"""

import sys
from pathlib import Path
import json

# Add backend to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from src.ml_room_detector import MLRoomDetector
import cv2

# Configuration
MODEL_PATH = project_root / "ml" / "models" / "sagemaker" / "train" / "weights" / "best.pt"
TEST_IMAGE = project_root / "ml" / "datasets" / "yolo_format" / "images" / "test" / "20023.png"
CONFIDENCE_THRESHOLD = 0.05
OUTPUT_DIR = project_root / "ml" / "results"

def test_model(image_path: str, model_path: str = None, confidence: float = 0.05, save_results: bool = True):
    """
    Test the model on a floor plan image.
    
    Args:
        image_path: Path to the test image
        model_path: Path to model file (default: uses MODEL_PATH)
        confidence: Confidence threshold for detections
        save_results: Whether to save results to JSON file
    """
    print("=" * 60)
    print("🧪 YOLOv8 Room Detection Test")
    print("=" * 60)
    print()
    
    # Use provided model path or default
    if model_path is None:
        model_path = str(MODEL_PATH)
    else:
        model_path = str(Path(model_path))
    
    # Check model exists
    if not Path(model_path).exists():
        print(f"❌ Model not found at: {model_path}")
        print(f"   Please ensure the model is trained and available.")
        return
    
    print(f"📦 Model: {model_path}")
    print(f"🖼️  Image: {image_path}")
    print(f"📊 Confidence: {confidence}")
    print()
    
    # Check image exists
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        print(f"❌ Image not found at: {image_path}")
        return
    
    # Initialize detector
    try:
        print("📦 Loading model...")
        detector = MLRoomDetector(model_path=model_path)
        print("✅ Model loaded successfully!")
        print()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Load image
    print(f"🖼️  Loading image: {image_path}")
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Could not load image from: {image_path}")
        return
    
    img_height, img_width = image.shape[:2]
    print(f"✅ Image loaded: {img_width}x{img_height} pixels")
    print()
    
    # Detect rooms
    print(f"🔍 Detecting rooms (confidence threshold: {confidence})...")
    rooms = detector.detect_rooms(image, confidence_threshold=confidence)
    print(f"✅ Detection complete!")
    print()
    
    # Display results
    print("=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print(f"   Total rooms detected: {len(rooms)}")
    print()
    
    if rooms:
        print("   Top 10 rooms (by confidence):")
        # Sort by confidence
        sorted_rooms = sorted(rooms, key=lambda x: x['confidence'], reverse=True)
        for i, room in enumerate(sorted_rooms[:10], 1):
            polygon = room['polygon']
            x_coords = [p[0] for p in polygon]
            y_coords = [p[1] for p in polygon]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            print(f"   Room {i}:")
            print(f"     - Confidence: {room['confidence']:.4f}")
            print(f"     - Polygon points: {len(polygon)}")
            print(f"     - Bounding box: ({min_x}, {min_y}) to ({max_x}, {max_y})")
            print(f"     - Size: {max_x - min_x}x{max_y - min_y} pixels")
            print()
        
        if len(rooms) > 10:
            print(f"   ... and {len(rooms) - 10} more rooms")
            print()
        
        # Convert to bounding boxes for API format
        print("🔄 Converting to API format (bounding boxes)...")
        converted = detector.convert_to_bounding_boxes(rooms, normalize=True)
        print(f"✅ Converted {len(converted)} rooms to normalized bounding boxes")
        print()
        
        # Show sample API response
        print("📋 Sample API Response (first 3 rooms):")
        for room in converted[:3]:
            print(f"   {json.dumps(room, indent=6)}")
        print()
        
        # Save results if requested
        if save_results:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = OUTPUT_DIR / f"test_results_{Path(image_path).stem}.json"
            
            results = {
                "image_path": str(image_path),
                "image_size": {"width": img_width, "height": img_height},
                "confidence_threshold": confidence,
                "total_rooms": len(rooms),
                "rooms": converted,
                "raw_rooms": rooms
            }
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"💾 Results saved to: {output_file}")
            print()
    else:
        print("   ⚠️  No rooms detected!")
        print()
        print("   💡 Suggestions:")
        print("      - Try lowering confidence threshold (e.g., 0.01)")
        print("      - Check if the image is a valid floor plan")
        print("      - Verify the model is working correctly")
        print()
    
    print("=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test the fine-tuned YOLOv8 room detection model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Test with default image
  python {Path(__file__).name}
  
  # Test with custom image
  python {Path(__file__).name} --image path/to/floorplan.png
  
  # Test with custom confidence
  python {Path(__file__).name} --image path/to/floorplan.png --confidence 0.01
  
  # Test without saving results
  python {Path(__file__).name} --image path/to/floorplan.png --no-save
        """
    )
    
    parser.add_argument(
        "--image",
        type=str,
        default=str(TEST_IMAGE),
        help=f"Path to test image (default: {TEST_IMAGE})"
    )
    
    parser.add_argument(
        "--confidence",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help=f"Confidence threshold (default: {CONFIDENCE_THRESHOLD})"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to JSON file"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=str(MODEL_PATH),
        help=f"Path to model file (default: {MODEL_PATH})"
    )
    
    args = parser.parse_args()
    
    test_model(
        image_path=args.image,
        model_path=args.model,
        confidence=args.confidence,
        save_results=not args.no_save
    )

