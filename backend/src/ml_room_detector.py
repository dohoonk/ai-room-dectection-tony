"""
ML-based room detection using YOLOv8 segmentation model.

This module provides room detection using a trained YOLOv8 model
instead of graph-based cycle detection.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from ultralytics import YOLO
import os


class MLRoomDetector:
    """Room detector using YOLOv8 segmentation model."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ML room detector.
        
        Args:
            model_path: Path to YOLOv8 model (.pt file). 
                       If None, uses default model location.
        """
        if model_path is None:
            # Default to SageMaker trained model
            project_root = Path(__file__).parent.parent.parent
            model_path = project_root / "ml" / "models" / "sagemaker" / "train" / "weights" / "best.pt"
        
        self.model_path = str(model_path)
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at: {self.model_path}")
        
        print(f"📦 Loading YOLOv8 model from {self.model_path}...")
        self.model = YOLO(self.model_path)
        print("✅ Model loaded successfully")
    
    def denormalize_polygon(
        self,
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
        self,
        results,
        img_width: int,
        img_height: int,
        confidence_threshold: float = 0.05
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
                if hasattr(result.masks, 'xy') and len(result.masks.xy) > i:
                    # result.masks.xy[i] returns pixel coordinates (already in original image size)
                    # Shape: (N, 2) where N is number of points, each point is [x, y]
                    # It's already a numpy array, no need for .cpu() or .numpy()
                    polygon_array = result.masks.xy[i]
                    if hasattr(polygon_array, 'cpu'):
                        polygon_array = polygon_array.cpu().numpy()
                    elif not isinstance(polygon_array, np.ndarray):
                        polygon_array = np.array(polygon_array)
                    polygon = [(int(point[0]), int(point[1])) for point in polygon_array]
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
    
    def detect_rooms(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.05,
        imgsz: int = 1024
    ) -> List[Dict[str, Any]]:
        """
        Detect rooms in a floor plan image.
        
        Args:
            image: Input image as numpy array (BGR format from cv2.imread)
            confidence_threshold: Minimum confidence for detections (default: 0.05)
            imgsz: Image size for inference (model will resize)
        
        Returns:
            List of room dictionaries with:
            - room_id: Unique identifier
            - polygon: List of (x, y) coordinates
            - confidence: Detection confidence score
        """
        img_height, img_width = image.shape[:2]
        
        # Run inference with low confidence to get all detections, then filter by our threshold
        # YOLOv8's conf parameter filters before returning, so use a very low value
        results = self.model(image, conf=0.001, imgsz=imgsz, verbose=False)
        
        # Extract polygons
        rooms = self.extract_polygons_from_predictions(
            results,
            img_width,
            img_height,
            confidence_threshold
        )
        
        return rooms
    
    def detect_rooms_from_file(
        self,
        image_path: str,
        confidence_threshold: float = 0.05,
        imgsz: int = 1024
    ) -> List[Dict[str, Any]]:
        """
        Detect rooms from an image file.
        
        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence for detections
            imgsz: Image size for inference
        
        Returns:
            List of room dictionaries
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from: {image_path}")
        
        return self.detect_rooms(image, confidence_threshold, imgsz)
    
    def convert_to_bounding_boxes(
        self,
        rooms: List[Dict[str, Any]],
        normalize: bool = True,
        target_range: Tuple[int, int] = (0, 1000)
    ) -> List[Dict[str, Any]]:
        """
        Convert room polygons to bounding boxes in normalized format.
        
        Args:
            rooms: List of room dictionaries with polygons
            normalize: Whether to normalize coordinates to 0-1000 range
            target_range: Target coordinate range for normalization
        
        Returns:
            List of rooms with bounding boxes instead of polygons
        """
        converted_rooms = []
        
        for i, room in enumerate(rooms):
            polygon = room['polygon']
            
            if len(polygon) < 3:
                continue
            
            # Calculate bounding box
            x_coords = [p[0] for p in polygon]
            y_coords = [p[1] for p in polygon]
            
            min_x = min(x_coords)
            min_y = min(y_coords)
            max_x = max(x_coords)
            max_y = max(y_coords)
            
            bbox = [min_x, min_y, max_x, max_y]
            
            # Normalize if requested
            if normalize:
                # Get original image dimensions (approximate from bbox)
                # In practice, you'd pass image dimensions separately
                img_width = max_x
                img_height = max_y
                
                # Normalize to 0-1000 range
                scale_x = target_range[1] / img_width if img_width > 0 else 1.0
                scale_y = target_range[1] / img_height if img_height > 0 else 1.0
                scale = min(scale_x, scale_y)
                
                bbox = [
                    min_x * scale,
                    min_y * scale,
                    max_x * scale,
                    max_y * scale
                ]
            
            converted_rooms.append({
                "id": f"room_{i+1:03d}",
                "bounding_box": bbox,
                "name_hint": f"Room {i+1}",
                "confidence": room.get("confidence", 0.0),
                "polygon": polygon  # Keep original polygon for reference
            })
        
        return converted_rooms


