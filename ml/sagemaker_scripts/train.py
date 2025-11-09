#!/usr/bin/env python3
"""
SageMaker Training Script for YOLOv8 Room Detection

This script runs on the SageMaker training instance.
It downloads the dataset from S3 and trains the model.
"""

import os
import subprocess
import sys

def install_dependencies():
    """Install required packages on SageMaker instance."""
    print("📦 Installing dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "ultralytics", "opencv-python", "numpy", "tqdm", "-q"
    ])

def download_dataset():
    """Download dataset from S3 to local instance."""
    print("📥 Downloading dataset from S3...")
    
    # SageMaker sets these environment variables
    training_data = os.environ.get("SM_CHANNEL_TRAINING", "/opt/ml/input/data/training")
    
    # Dataset should already be mounted at this location
    # But we'll verify it exists
    if os.path.exists(training_data):
        print(f"✅ Dataset found at: {training_data}")
        return training_data
    else:
        raise FileNotFoundError(f"Dataset not found at {training_data}")

def train_model(dataset_path):
    """Train YOLOv8 model."""
    print("🚀 Starting YOLOv8 training...")
    
    # Find data.yaml
    data_yaml = os.path.join(dataset_path, "data.yaml")
    if not os.path.exists(data_yaml):
        raise FileNotFoundError(f"data.yaml not found at {data_yaml}")
    
    # Read and update data.yaml paths
    with open(data_yaml, 'r') as f:
        content = f.read()
    
    # Update path in data.yaml to point to mounted dataset
    # SageMaker mounts data at /opt/ml/input/data/training
    import re
    # Replace the path line
    content = re.sub(
        r'path:.*',
        f'path: {dataset_path}',
        content
    )
    
    # Write updated data.yaml to a temp location
    updated_yaml = "/tmp/data.yaml"
    with open(updated_yaml, 'w') as f:
        f.write(content)
    
    print(f"📝 Updated data.yaml:")
    print(f"   Dataset path: {dataset_path}")
    print(f"   Config saved to: {updated_yaml}")
    
    # Training parameters from hyperparameters
    epochs = int(os.environ.get("SM_HP_EPOCHS", "50"))
    imgsz = int(os.environ.get("SM_HP_IMGSZ", "1024"))
    batch = int(os.environ.get("SM_HP_BATCH", "8"))
    model = os.environ.get("SM_HP_MODEL", "yolov8n-seg.pt")
    
    # Run YOLOv8 training
    cmd = [
        "yolo", "segment", "train",
        f"model={model}",
        f"data={updated_yaml}",
        f"epochs={epochs}",
        f"imgsz={imgsz}",
        f"batch={batch}",
        "project=/opt/ml/model",
        "name=train"
    ]
    
    print(f"📝 Training command: {' '.join(cmd)}")
    print()
    subprocess.check_call(cmd)

def save_model():
    """Save model to SageMaker output directory."""
    print("💾 Saving model...")
    
    model_dir = "/opt/ml/model"
    output_dir = "/opt/ml/output"
    
    # Copy best model to output directory
    best_model = os.path.join(model_dir, "train", "weights", "best.pt")
    if os.path.exists(best_model):
        import shutil
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy(best_model, os.path.join(output_dir, "best.pt"))
        print(f"✅ Model saved to {output_dir}/best.pt")
    else:
        print("⚠️  Warning: best.pt not found")

def main():
    """Main training function."""
    print("="*60)
    print("🚀 SageMaker YOLOv8 Training")
    print("="*60)
    
    try:
        # Install dependencies
        install_dependencies()
        
        # Download dataset
        dataset_path = download_dataset()
        
        # Train model
        train_model(dataset_path)
        
        # Save model
        save_model()
        
        print("="*60)
        print("✅ Training completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

