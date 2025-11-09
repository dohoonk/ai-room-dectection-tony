#!/usr/bin/env python3
"""
Launch YOLOv8 Training Job on SageMaker

This script runs on your local machine and creates a SageMaker training job.
"""

import boto3
import sagemaker
from sagemaker.estimator import Estimator
from sagemaker import get_execution_role
import time
import os
from pathlib import Path

def get_or_create_role():
    """Get SageMaker execution role."""
    try:
        # Try to get default role
        role = get_execution_role()
        print(f"✅ Using role: {role}")
        return role
    except ValueError:
        # If no default role, you need to specify one
        print("⚠️  No default SageMaker role found.")
        print("   Please create a role in IAM and provide the ARN.")
        print("   Or set SAGEMAKER_ROLE_ARN environment variable.")
        
        role_arn = os.environ.get("SAGEMAKER_ROLE_ARN")
        if role_arn:
            return role_arn
        else:
            raise ValueError(
                "Please set SAGEMAKER_ROLE_ARN environment variable or "
                "create a default SageMaker role in IAM."
            )

def upload_training_script(s3_bucket, s3_prefix="training-scripts"):
    """Upload training script to S3."""
    s3 = boto3.client('s3')
    
    script_path = Path(__file__).parent / "train.py"
    s3_key = f"{s3_prefix}/train.py"
    
    print(f"📤 Uploading training script to s3://{s3_bucket}/{s3_key}...")
    s3.upload_file(str(script_path), s3_bucket, s3_key)
    
    return f"s3://{s3_bucket}/{s3_key}"

def create_training_job(
    s3_bucket,
    dataset_s3_path,
    instance_type="ml.g4dn.xlarge",
    use_spot=False,
    epochs=50,
    imgsz=1024,
    batch=8,
    model="yolov8n-seg.pt"
):
    """Create and launch SageMaker training job."""
    
    # Get SageMaker session and role
    sess = sagemaker.Session()
    role = get_or_create_role()
    
    # Upload training script
    script_uri = upload_training_script(s3_bucket)
    
    # Use PyTorch framework (easier than custom container)
    from sagemaker.pytorch import PyTorch
    
    # Create estimator using PyTorch framework
    estimator = PyTorch(
        entry_point="train.py",
        source_dir=str(Path(__file__).parent),
        role=role,
        framework_version="2.0.1",
        py_version="py310",
        instance_count=1,
        instance_type=instance_type,
        use_spot_instances=use_spot,
        max_wait=36000 if use_spot else None,  # 10 hours max wait for spot
        max_run=36000,  # 10 hours max run time
        output_path=f"s3://{s3_bucket}/training-output",
        sagemaker_session=sess,
        hyperparameters={
            "epochs": str(epochs),
            "imgsz": str(imgsz),
            "batch": str(batch),
            "model": model
        }
    )
    
    # Define input data channels
    # SageMaker will mount this at /opt/ml/input/data/training
    from sagemaker.inputs import TrainingInput
    inputs = {
        "training": TrainingInput(
            s3_data=dataset_s3_path,
            content_type="application/x-directory"
        )
    }
    
    # Launch training job
    print(f"🚀 Launching training job on {instance_type}...")
    print(f"   Dataset: {dataset_s3_path}")
    print(f"   Epochs: {epochs}")
    print(f"   Using Spot: {use_spot}")
    print()
    
    estimator.fit(inputs, wait=False)
    
    job_name = estimator.latest_training_job.name
    print(f"✅ Training job created: {job_name}")
    print(f"📊 Monitor at: https://console.aws.amazon.com/sagemaker/home?region={sess.boto_region_name}#/training-jobs/{job_name}")
    
    return estimator, job_name

def monitor_training(estimator):
    """Monitor training job progress."""
    print("\n📊 Monitoring training...")
    print("   (Press Ctrl+C to stop monitoring, training will continue)")
    print()
    
    try:
        # Use fit() with wait=True or check status manually
        import time
        job_name = estimator.latest_training_job.name
        print(f"   Job: {job_name}")
        print("   Checking status every 30 seconds...")
        print()
        
        while True:
            status = estimator.latest_training_job.describe()['TrainingJobStatus']
            print(f"   Status: {status}", end='\r')
            
            if status in ['Completed', 'Failed', 'Stopped']:
                print(f"\n   Final status: {status}")
                if status == 'Completed':
                    print("\n✅ Training completed!")
                    return True
                else:
                    print(f"\n⚠️  Training {status.lower()}")
                    return False
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n⚠️  Monitoring stopped. Training continues in background.")
        print(f"   Job name: {estimator.latest_training_job.name}")
        return False

def download_model(estimator, local_path="ml/models/sagemaker"):
    """Download trained model from S3."""
    print("\n📥 Downloading model...")
    
    model_path = Path(local_path)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Model is saved to S3 output path
    s3_model_path = estimator.model_data
    print(f"   Model location: {s3_model_path}")
    
    # Download using AWS CLI (easier than boto3 for tar files)
    import subprocess
    subprocess.check_call([
        "aws", "s3", "cp", s3_model_path,
        str(model_path / "model.tar.gz")
    ])
    
    print(f"✅ Model downloaded to {model_path}/model.tar.gz")
    print(f"   Extract with: tar -xzf {model_path}/model.tar.gz")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch YOLOv8 training on SageMaker")
    parser.add_argument("--bucket", type=str, required=True,
                       help="S3 bucket name (e.g., room-detection-training-123)")
    parser.add_argument("--dataset-path", type=str, 
                       default="yolo_format",
                       help="S3 path to dataset (default: yolo_format)")
    parser.add_argument("--instance-type", type=str,
                       default="ml.g4dn.xlarge",
                       help="SageMaker instance type (default: ml.g4dn.xlarge)")
    parser.add_argument("--spot", action="store_true",
                       help="Use Spot instances (70-90% cheaper)")
    parser.add_argument("--epochs", type=int, default=50,
                       help="Number of epochs (default: 50)")
    parser.add_argument("--imgsz", type=int, default=1024,
                       help="Image size (default: 1024)")
    parser.add_argument("--batch", type=int, default=8,
                       help="Batch size (default: 8)")
    parser.add_argument("--model", type=str, default="yolov8n-seg.pt",
                       help="YOLOv8 model (default: yolov8n-seg.pt)")
    parser.add_argument("--no-wait", action="store_true",
                       help="Don't wait for training to complete")
    parser.add_argument("--download", action="store_true",
                       help="Download model when training completes")
    
    args = parser.parse_args()
    
    # Construct dataset S3 path
    dataset_s3_path = f"s3://{args.bucket}/{args.dataset_path}"
    
    print("="*60)
    print("🚀 SageMaker YOLOv8 Training Launcher")
    print("="*60)
    print(f"   Bucket: {args.bucket}")
    print(f"   Dataset: {dataset_s3_path}")
    print(f"   Instance: {args.instance_type}")
    print(f"   Spot: {args.spot}")
    print(f"   Epochs: {args.epochs}")
    print("="*60)
    print()
    
    # Create training job
    estimator, job_name = create_training_job(
        s3_bucket=args.bucket,
        dataset_s3_path=dataset_s3_path,
        instance_type=args.instance_type,
        use_spot=args.spot,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        model=args.model
    )
    
    # Monitor training
    if not args.no_wait:
        completed = monitor_training(estimator)
        
        if completed and args.download:
            download_model(estimator)
    else:
        print(f"\n✅ Training job launched: {job_name}")
        print("   Check status with: aws sagemaker describe-training-job --training-job-name", job_name)

if __name__ == "__main__":
    main()

