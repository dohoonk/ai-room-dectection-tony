#!/usr/bin/env python3
"""
Convert CubiCasa5K dataset to YOLOv8 segmentation format.

WHAT THIS SCRIPT DOES:
1. Reads CubiCasa5K dataset (SVG files with room polygons, PNG floor plans)
2. Parses SVG files to extract room polygons
3. Converts to YOLOv8 polygon format
4. Creates proper directory structure for YOLOv8 training
5. Generates label files (.txt) with polygon coordinates

YOLOv8 FORMAT EXPLANATION:
Each label file contains one line per room:
<class_id> x1 y1 x2 y2 x3 y3 x4 y4 ...
- class_id: Always 0 (we detect all rooms as one class, then use OCR for labels)
- x1 y1 x2 y2...: Normalized polygon coordinates (0.0 to 1.0)

DATASET STRUCTURE:
cubicasa5k/
├── cubicasa5k/
│   ├── high_quality/[ID]/
│   │   ├── F1_original.png
│   │   ├── F1_scaled.png
│   │   └── model.svg
│   ├── colorful/[ID]/
│   └── high_quality_architectural/[ID]/
├── train.txt  (list of paths like /high_quality/3954/)
├── val.txt
└── test.txt
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import argparse
from tqdm import tqdm
import xml.etree.ElementTree as ET
import re

def parse_svg_polygon(points_str: str) -> List[Tuple[float, float]]:
    """
    Parse SVG polygon points string to list of (x, y) tuples.
    
    Format: "x1,y1 x2,y2 x3,y3 ..." or "x1 y1 x2 y2 x3 y3 ..."
    """
    polygon = []
    
    # Handle both comma-separated and space-separated formats
    # First, try to split by spaces
    coords = re.split(r'[\s,]+', points_str.strip())
    
    # Remove empty strings
    coords = [c for c in coords if c]
    
    # Parse pairs of coordinates
    for i in range(0, len(coords), 2):
        if i + 1 < len(coords):
            try:
                x = float(coords[i])
                y = float(coords[i + 1])
                polygon.append((x, y))
            except ValueError:
                continue
    
    return polygon

def extract_rooms_from_svg(svg_path: Path) -> List[Dict[str, Any]]:
    """
    Extract room polygons from SVG file.
    
    SVG structure:
    <g class="Space [RoomType]">
        <polygon points="x1,y1 x2,y2 ..."/>
    </g>
    
    Returns:
        List of room dictionaries with polygon coordinates and room type
    """
    if not svg_path.exists():
        print(f"❌ Error: SVG file not found: {svg_path}")
        return []
    
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"❌ Error parsing SVG {svg_path}: {e}")
        return []
    
    # Get SVG viewBox or dimensions
    viewbox = root.get('viewBox', '')
    width = float(root.get('width', '1000'))
    height = float(root.get('height', '1000'))
    
    if viewbox:
        # Parse viewBox: "x y width height"
        vb_parts = viewbox.split()
        if len(vb_parts) == 4:
            width = float(vb_parts[2])
            height = float(vb_parts[3])
    
    rooms = []
    
    # Find all Space elements (rooms)
    # SVG namespace handling
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Find all groups with class containing "Space"
    for elem in root.iter():
        # Check if this is a Space element
        class_attr = elem.get('class', '')
        if 'Space' in class_attr:
            # Extract room type from class (e.g., "Space Kitchen" -> "Kitchen")
            room_type = 'room'  # Default
            class_parts = class_attr.split()
            for part in class_parts:
                if part != 'Space' and not part.startswith('Space'):
                    room_type = part
                    break
            
            # Find polygon within this Space element
            for polygon_elem in elem.iter():
                if polygon_elem.tag.endswith('polygon'):
                    points_str = polygon_elem.get('points', '')
                    if points_str:
                        polygon = parse_svg_polygon(points_str)
                        if len(polygon) >= 3:  # At least 3 points for a valid polygon
                            rooms.append({
                                'polygon': polygon,
                                'room_type': room_type,
                                'class': class_attr
                            })
    
    return rooms

def normalize_polygon(polygon: List[Tuple[float, float]], img_width: int, img_height: int) -> List[float]:
    """
    Convert polygon coordinates to YOLOv8 format (normalized 0.0-1.0).
    
    YOLOv8 requires:
    - Coordinates normalized to image size (0.0 to 1.0)
    - Format: [x1, y1, x2, y2, x3, y3, ...]
    """
    normalized = []
    for x, y in polygon:
        # Normalize: divide by image dimensions
        norm_x = x / img_width
        norm_y = y / img_height
        
        # Ensure values are between 0 and 1
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))
        
        normalized.extend([norm_x, norm_y])
    
    return normalized

def write_yolo_label(rooms: List[Dict[str, Any]], label_path: Path, img_width: int, img_height: int):
    """
    Write YOLOv8 format label file.
    
    Format per line:
    <class_id> x1 y1 x2 y2 x3 y3 ...
    
    We use class_id = 0 for all rooms (we'll use OCR later to identify room types)
    """
    with open(label_path, 'w') as f:
        for room in rooms:
            polygon = room['polygon']
            normalized = normalize_polygon(polygon, img_width, img_height)
            
            # Format: class_id x1 y1 x2 y2 ...
            line = '0 ' + ' '.join([f'{coord:.6f}' for coord in normalized])
            f.write(line + '\n')

def load_split_file(split_file: Path) -> List[str]:
    """
    Load split file (train.txt, val.txt, test.txt).
    
    Format: Each line contains a path like /high_quality/3954/
    """
    if not split_file.exists():
        return []
    
    paths = []
    with open(split_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                paths.append(line)
    
    return paths

def find_sample_files(base_dir: Path, sample_path: str) -> Optional[Dict[str, Path]]:
    """
    Find files for a sample given its path (e.g., /high_quality/3954/).
    
    Returns:
        Dictionary with 'floorplan', 'svg' paths, or None if not found
    """
    # Remove leading slash if present
    sample_path = sample_path.lstrip('/')
    sample_dir = base_dir / 'cubicasa5k' / sample_path
    
    if not sample_dir.exists():
        return None
    
    # Look for floorplan image (prefer F1_original.png, fallback to F1_scaled.png)
    floorplan = None
    for img_name in ['F1_original.png', 'F1_scaled.png']:
        img_path = sample_dir / img_name
        if img_path.exists():
            floorplan = img_path
            break
    
    # Look for SVG file
    svg_path = sample_dir / 'model.svg'
    
    if not floorplan or not svg_path.exists():
        return None
    
    return {
        'floorplan': floorplan,
        'svg': svg_path,
        'sample_id': sample_dir.name
    }

def convert_split(
    cubicasa_dir: Path,
    split_name: str,
    split_paths: List[str],
    output_dir: Path,
    max_samples: int = None
) -> Tuple[int, int]:
    """
    Convert one split (train/val/test) from CubiCasa5K to YOLOv8 format.
    
    Args:
        cubicasa_dir: Path to CubiCasa5K root directory
        split_name: Name of split ('train', 'val', 'test')
        split_paths: List of sample paths from split file
        output_dir: Output directory for YOLOv8 dataset
        max_samples: Maximum number of samples to process (None = all)
    
    Returns:
        Tuple of (successful_conversions, failed_conversions)
    """
    # Create output directories
    images_output = output_dir / 'images' / split_name
    labels_output = output_dir / 'labels' / split_name
    images_output.mkdir(parents=True, exist_ok=True)
    labels_output.mkdir(parents=True, exist_ok=True)
    
    if max_samples:
        split_paths = split_paths[:max_samples]
    
    successful = 0
    failed = 0
    
    print(f"\n📁 Processing {split_name} split...")
    print(f"   Found {len(split_paths)} samples")
    
    for sample_path in tqdm(split_paths, desc=f"Converting {split_name}"):
        try:
            # Find sample files
            files = find_sample_files(cubicasa_dir, sample_path)
            if not files:
                failed += 1
                continue
            
            floorplan_path = files['floorplan']
            svg_path = files['svg']
            sample_id = files['sample_id']
            
            # Load floorplan image to get dimensions
            floorplan_img = cv2.imread(str(floorplan_path))
            if floorplan_img is None:
                print(f"⚠️  Warning: Could not load floorplan: {floorplan_path}")
                failed += 1
                continue
            
            img_height, img_width = floorplan_img.shape[:2]
            
            # Extract room polygons from SVG
            rooms = extract_rooms_from_svg(svg_path)
            
            if not rooms:
                print(f"⚠️  Warning: No rooms found in {sample_path}")
                failed += 1
                continue
            
            # Copy floorplan image to output
            output_image_path = images_output / f"{sample_id}.png"
            cv2.imwrite(str(output_image_path), floorplan_img)
            
            # Write YOLOv8 label file
            label_path = labels_output / f"{sample_id}.txt"
            write_yolo_label(rooms, label_path, img_width, img_height)
            
            successful += 1
            
        except Exception as e:
            print(f"❌ Error processing {sample_path}: {str(e)}")
            failed += 1
            continue
    
    print(f"✅ {split_name}: {successful} successful, {failed} failed")
    return successful, failed

def create_data_yaml(output_dir: Path, num_classes: int = 1):
    """
    Create data.yaml file required by YOLOv8.
    """
    yaml_content = f"""# YOLOv8 Dataset Configuration
# This file tells YOLOv8 where to find your training data

# Paths to images (relative to this file or absolute)
path: {output_dir.absolute()}
train: images/train
val: images/val
test: images/test  # optional

# Number of classes
nc: {num_classes}

# Class names
names:
  0: room  # We detect all rooms as one class, then use OCR for room type

# Image size for training (you can adjust this)
# YOLOv8 will resize images to this size during training
imgsz: 1024
"""
    
    yaml_path = output_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"✅ Created data.yaml at {yaml_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Convert CubiCasa5K dataset to YOLOv8 segmentation format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python ml/scripts/convert_cubicasa_to_yolo.py \\
    --input ml/datasets/archive/cubicasa5k \\
    --output ml/datasets/yolo_format \\
    --max-samples 100

This will:
  1. Read CubiCasa5K dataset from input directory
  2. Parse SVG files to extract room polygons
  3. Convert to YOLOv8 polygon format
  4. Create YOLOv8 dataset structure in output directory
  5. Generate data.yaml configuration file
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to CubiCasa5K dataset root directory (should contain cubicasa5k/ folder with train.txt, val.txt, test.txt)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='ml/datasets/yolo_format',
        help='Output directory for YOLOv8 format dataset (default: ml/datasets/yolo_format)'
    )
    
    parser.add_argument(
        '--max-samples',
        type=int,
        default=None,
        help='Maximum number of samples per split to process (useful for testing, default: all)'
    )
    
    parser.add_argument(
        '--splits',
        nargs='+',
        default=['train', 'val', 'test'],
        help='Which splits to convert (default: train val test)'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"❌ Error: Input directory does not exist: {input_dir}")
        return
    
    # Check for split files
    cubicasa_base = input_dir / 'cubicasa5k'
    if not cubicasa_base.exists():
        print(f"❌ Error: cubicasa5k folder not found in {input_dir}")
        print(f"   Expected: {cubicasa_base}")
        return
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Converting CubiCasa5K to YOLOv8 format...")
    print(f"   Input: {input_dir}")
    print(f"   Output: {output_dir}")
    print()
    
    total_successful = 0
    total_failed = 0
    
    # Convert each split
    for split_name in args.splits:
        split_file = cubicasa_base / f"{split_name}.txt"
        
        if not split_file.exists():
            print(f"⚠️  Warning: Split file not found: {split_file}")
            continue
        
        # Load split paths
        split_paths = load_split_file(split_file)
        
        if not split_paths:
            print(f"⚠️  Warning: No paths found in {split_file}")
            continue
        
        # Convert split
        successful, failed = convert_split(
            input_dir,
            split_name,
            split_paths,
            output_dir,
            max_samples=args.max_samples
        )
        total_successful += successful
        total_failed += failed
    
    # Create data.yaml
    print("\n📝 Creating data.yaml...")
    create_data_yaml(output_dir)
    
    # Summary
    print("\n" + "="*60)
    print("✅ Conversion Complete!")
    print(f"   Total successful: {total_successful}")
    print(f"   Total failed: {total_failed}")
    print(f"\n📁 Output directory: {output_dir}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review the converted data in: {output_dir}")
    print(f"   2. Check data.yaml configuration")
    print(f"   3. Train your model (see TRAINING_GUIDE.md)")
    print("="*60)

if __name__ == '__main__':
    main()
