#!/usr/bin/env python3
"""
Script to prepare 50 floor plan images for SageMaker training.

This script helps organize images and create annotations for training.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any
import argparse

def create_directory_structure(output_dir: str):
    """Create the directory structure for training data."""
    splits = ['train', 'validation', 'test']
    subdirs = ['images', 'annotations', 'masks']
    
    for split in splits:
        for subdir in subdirs:
            dir_path = Path(output_dir) / split / subdir
            dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created directory structure in {output_dir}")

def organize_images(input_dir: str, output_dir: str, train_ratio: float = 0.8, val_ratio: float = 0.1):
    """
    Organize images into train/validation/test splits.
    
    Args:
        input_dir: Directory containing input images
        output_dir: Output directory for organized data
        train_ratio: Ratio of images for training (default: 0.8)
        val_ratio: Ratio of images for validation (default: 0.1)
    """
    input_path = Path(input_dir)
    image_files = sorted([f for f in input_path.glob('*.png') + input_path.glob('*.jpg') + input_path.glob('*.jpeg')])
    
    if not image_files:
        print(f"❌ No images found in {input_dir}")
        return
    
    total = len(image_files)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)
    test_count = total - train_count - val_count
    
    print(f"📊 Found {total} images")
    print(f"   Training: {train_count} ({train_ratio*100:.0f}%)")
    print(f"   Validation: {val_count} ({val_ratio*100:.0f}%)")
    print(f"   Test: {test_count} ({(1-train_ratio-val_ratio)*100:.0f}%)")
    
    # Copy images to appropriate directories
    for i, image_file in enumerate(image_files):
        if i < train_count:
            split = 'train'
        elif i < train_count + val_count:
            split = 'validation'
        else:
            split = 'test'
        
        dest = Path(output_dir) / split / 'images' / image_file.name
        shutil.copy2(image_file, dest)
        print(f"   Copied {image_file.name} → {split}/images/")
    
    print(f"✅ Organized {total} images into splits")

def create_annotation_template(image_path: str, output_path: str):
    """
    Create a blank annotation template for an image.
    
    Args:
        image_path: Path to the image file
        output_path: Path to save the annotation JSON
    """
    template = {
        "image_id": Path(image_path).stem,
        "image_path": str(image_path),
        "walls": [
            # Example wall segment:
            # {
            #     "start": [100, 100],
            #     "end": [500, 100],
            #     "is_load_bearing": false
            # }
        ],
        "rooms": [
            # Example room:
            # {
            #     "id": "room_001",
            #     "bounding_box": [50, 50, 200, 300],
            #     "name_hint": "Bedroom"
            # }
        ],
        "notes": "Add wall segments and rooms here"
    }
    
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"✅ Created annotation template: {output_path}")

def create_all_annotation_templates(output_dir: str):
    """Create annotation templates for all images."""
    splits = ['train', 'validation', 'test']
    
    for split in splits:
        images_dir = Path(output_dir) / split / 'images'
        annotations_dir = Path(output_dir) / split / 'annotations'
        
        for image_file in images_dir.glob('*.png'):
            annotation_file = annotations_dir / f"{image_file.stem}.json"
            if not annotation_file.exists():
                create_annotation_template(str(image_file), str(annotation_file))
        
        for image_file in images_dir.glob('*.jpg'):
            annotation_file = annotations_dir / f"{image_file.stem}.json"
            if not annotation_file.exists():
                create_annotation_template(str(image_file), str(annotation_file))
        
        for image_file in images_dir.glob('*.jpeg'):
            annotation_file = annotations_dir / f"{image_file.stem}.json"
            if not annotation_file.exists():
                create_annotation_template(str(image_file), str(annotation_file))

def validate_annotations(output_dir: str) -> Dict[str, Any]:
    """Validate that all images have corresponding annotations."""
    splits = ['train', 'validation', 'test']
    results = {
        'total_images': 0,
        'annotated_images': 0,
        'missing_annotations': []
    }
    
    for split in splits:
        images_dir = Path(output_dir) / split / 'images'
        annotations_dir = Path(output_dir) / split / 'annotations'
        
        for image_file in images_dir.glob('*.*'):
            if image_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                results['total_images'] += 1
                annotation_file = annotations_dir / f"{image_file.stem}.json"
                
                if annotation_file.exists():
                    results['annotated_images'] += 1
                    # Validate JSON structure
                    try:
                        with open(annotation_file) as f:
                            data = json.load(f)
                            if 'walls' not in data or 'rooms' not in data:
                                results['missing_annotations'].append({
                                    'split': split,
                                    'image': image_file.name,
                                    'issue': 'Missing walls or rooms fields'
                                })
                    except json.JSONDecodeError:
                        results['missing_annotations'].append({
                            'split': split,
                            'image': image_file.name,
                            'issue': 'Invalid JSON'
                        })
                else:
                    results['missing_annotations'].append({
                        'split': split,
                        'image': image_file.name,
                        'issue': 'Annotation file not found'
                    })
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Prepare training data for SageMaker')
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Directory containing input images')
    parser.add_argument('--output-dir', type=str, default='datasets/training',
                        help='Output directory for organized data')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                        help='Ratio of images for training (default: 0.8)')
    parser.add_argument('--val-ratio', type=float, default=0.1,
                        help='Ratio of images for validation (default: 0.1)')
    parser.add_argument('--create-templates', action='store_true',
                        help='Create annotation templates for all images')
    parser.add_argument('--validate', action='store_true',
                        help='Validate annotations')
    
    args = parser.parse_args()
    
    print("🚀 Preparing training data for SageMaker...")
    print(f"   Input directory: {args.input_dir}")
    print(f"   Output directory: {args.output_dir}")
    print()
    
    # Create directory structure
    create_directory_structure(args.output_dir)
    print()
    
    # Organize images
    organize_images(args.input_dir, args.output_dir, args.train_ratio, args.val_ratio)
    print()
    
    # Create annotation templates if requested
    if args.create_templates:
        print("📝 Creating annotation templates...")
        create_all_annotation_templates(args.output_dir)
        print()
    
    # Validate annotations if requested
    if args.validate:
        print("✅ Validating annotations...")
        results = validate_annotations(args.output_dir)
        print(f"   Total images: {results['total_images']}")
        print(f"   Annotated images: {results['annotated_images']}")
        print(f"   Missing annotations: {len(results['missing_annotations'])}")
        
        if results['missing_annotations']:
            print("\n⚠️  Missing or invalid annotations:")
            for item in results['missing_annotations'][:10]:  # Show first 10
                print(f"   - {item['split']}/{item['image']}: {item['issue']}")
            if len(results['missing_annotations']) > 10:
                print(f"   ... and {len(results['missing_annotations']) - 10} more")
        print()
    
    print("✅ Data preparation complete!")
    print(f"\n📋 Next steps:")
    print(f"   1. Review and fill in annotations in {args.output_dir}")
    print(f"   2. Run --validate to check annotations")
    print(f"   3. Create masks from annotations (see SAGEMAKER_50_IMAGES_PLAN.md)")
    print(f"   4. Upload to S3 for SageMaker training")

if __name__ == '__main__':
    main()

