#!/usr/bin/env python3
"""
Extract room polygons from YOLOv8 predictions.

WHAT THIS DOES:
1. Loads a trained YOLOv8 model
2. Runs inference on a floor plan image
3. Converts YOLOv8 predictions to polygon coordinates
4. Returns polygons in a format ready for your application

OUTPUT FORMAT:
[
  {
    "room_id": 0,
    "polygon": [[x1, y1], [x2, y2], ...],  # Pixel coordinates
    "confidence": 0.95
  },
  ...
]
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
import argparse
from ultralytics import YOLO
import json

def denormalize_polygon(
    normalized_coords: List[float],
    img_width: int,
    img_height: int
) -> List[Tuple[int, int]]:
    """
    Convert normalized YOLOv8 coordinates (0.0-1.0) to pixel coordinates.
    
    YOLOv8 outputs: [x1, y1, x2, y2, x3, y3, ...]
    We convert to: [(x1, y1), (x2, y2), (x3, y3), ...]
    """
    polygon = []
    for i in range(0, len(normalized_coords), 2):
        x = int(normalized_coords[i] * img_width)
        y = int(normalized_coords[i + 1] * img_height)
        polygon.append((x, y))
    return polygon

def extract_polygons_from_predictions(
    results,
    img_width: int,
    img_height: int,
    confidence_threshold: float = 0.25
) -> List[Dict[str, Any]]:
    """
    Extract room polygons from YOLOv8 prediction results.
    
    Args:
        results: YOLOv8 prediction results object
        img_width: Original image width
        img_height: Original image height
        confidence_threshold: Minimum confidence to include a detection
    
    Returns:
        List of room dictionaries with polygons
    """
    rooms = []
    
    # YOLOv8 returns results for each image (we process one at a time)
    for result in results:
        # Get segmentation masks
        if result.masks is None:
            print("⚠️  Warning: No masks found in predictions")
            continue
        
        # Get masks and boxes
        masks = result.masks.data.cpu().numpy()  # Shape: (num_detections, H, W)
        boxes = result.boxes
        
        # Process each detected room
        for i, mask in enumerate(masks):
            # Get confidence score
            confidence = float(boxes.conf[i].cpu().numpy())
            
            # Filter by confidence
            if confidence < confidence_threshold:
                continue
            
            # Convert mask to polygon
            # Method 1: Use YOLOv8's built-in polygon extraction
            if hasattr(result.masks, 'xy'):
                # Get polygon coordinates (already normalized)
                polygon_normalized = result.masks.xy[i].flatten().tolist()
                polygon = denormalize_polygon(
                    polygon_normalized,
                    img_width,
                    img_height
                )
            else:
                # Method 2: Extract polygon from mask using OpenCV
                # Resize mask to original image size
                mask_resized = cv2.resize(
                    (mask * 255).astype(np.uint8),
                    (img_width, img_height),
                    interpolation=cv2.INTER_NEAREST
                )
                
                # Find contours
                contours, _ = cv2.findContours(
                    mask_resized,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                
                if not contours:
                    continue
                
                # Get largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Simplify polygon
                epsilon = 0.002 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                # Convert to list of tuples
                polygon = [(int(point[0][0]), int(point[0][1])) for point in approx]
            
            # Only add if polygon has at least 3 points
            if len(polygon) >= 3:
                rooms.append({
                    "room_id": len(rooms),
                    "polygon": polygon,
                    "confidence": confidence
                })
    
    return rooms

def predict_rooms(
    model_path: str,
    image_path: str,
    confidence_threshold: float = 0.25,
    imgsz: int = 1024
) -> List[Dict[str, Any]]:
    """
    Predict rooms in a floor plan image.
    
    Args:
        model_path: Path to trained YOLOv8 model (.pt file)
        image_path: Path to floor plan image
        confidence_threshold: Minimum confidence for detections
        imgsz: Image size for inference (model will resize)
    
    Returns:
        List of room dictionaries
    """
    # Load model
    print(f"📦 Loading model from {model_path}...")
    model = YOLO(model_path)
    
    # Load image to get original dimensions
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    img_height, img_width = img.shape[:2]
    print(f"📐 Image size: {img_width}x{img_height}")
    
    # Run inference
    print("🔍 Running inference...")
    results = model.predict(
        image_path,
        imgsz=imgsz,
        conf=confidence_threshold,
        save=False  # Set to True if you want to save visualization
    )
    
    # Extract polygons
    print("📝 Extracting polygons...")
    rooms = extract_polygons_from_predictions(
        results,
        img_width,
        img_height,
        confidence_threshold
    )
    
    print(f"✅ Found {len(rooms)} rooms")
    return rooms

def visualize_predictions(
    image_path: str,
    rooms: List[Dict[str, Any]],
    output_path: str
):
    """
    Draw room polygons on image for visualization.
    
    Args:
        image_path: Path to original image
        rooms: List of room dictionaries
        output_path: Where to save visualization
    """
    img = cv2.imread(image_path)
    
    # Draw each room polygon
    for i, room in enumerate(rooms):
        polygon = np.array(room['polygon'], dtype=np.int32)
        confidence = room['confidence']
        
        # Choose color based on room index
        colors = [
            (255, 0, 0),    # Blue
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]
        color = colors[i % len(colors)]
        
        # Draw filled polygon
        cv2.fillPoly(img, [polygon], color)
        
        # Draw polygon outline
        cv2.polylines(img, [polygon], True, (0, 0, 0), 2)
        
        # Add confidence label
        if polygon.size > 0:
            centroid = polygon.mean(axis=0).astype(int)
            cv2.putText(
                img,
                f"Room {i} ({confidence:.2f})",
                tuple(centroid),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
    
    # Save visualization
    cv2.imwrite(output_path, img)
    print(f"💾 Saved visualization to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Extract room polygons from floor plan using trained YOLOv8 model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Basic prediction
  python ml/scripts/extract_polygons.py \\
    --model ml/models/best.pt \\
    --image path/to/floorplan.png \\
    --output ml/results/results.json

  # With visualization
  python ml/scripts/extract_polygons.py \\
    --model ml/models/best.pt \\
    --image path/to/floorplan.png \\
    --output ml/results/results.json \\
    --visualize ml/results/output.png \\
    --confidence 0.3
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained YOLOv8 model (.pt file)'
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
        default='results.json',
        help='Output JSON file path (default: results.json)'
    )
    
    parser.add_argument(
        '--visualize',
        type=str,
        default=None,
        help='Optional: Save visualization image to this path'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.25,
        help='Confidence threshold (0.0-1.0, default: 0.25)'
    )
    
    parser.add_argument(
        '--imgsz',
        type=int,
        default=1024,
        help='Image size for inference (default: 1024)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.model).exists():
        print(f"❌ Error: Model file not found: {args.model}")
        return
    
    if not Path(args.image).exists():
        print(f"❌ Error: Image file not found: {args.image}")
        return
    
    # Predict rooms
    rooms = predict_rooms(
        args.model,
        args.image,
        confidence_threshold=args.confidence,
        imgsz=args.imgsz
    )
    
    # Save results
    output_data = {
        "image_path": args.image,
        "num_rooms": len(rooms),
        "rooms": rooms
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"💾 Saved results to {args.output}")
    
    # Create visualization if requested
    if args.visualize:
        visualize_predictions(args.image, rooms, args.visualize)
    
    print("\n✅ Done!")
    print(f"   Found {len(rooms)} rooms")
    print(f"   Results saved to: {args.output}")

if __name__ == '__main__':
    main()

