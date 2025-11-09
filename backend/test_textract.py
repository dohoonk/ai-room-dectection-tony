"""
Manual test script for Amazon Textract integration.

This script tests Textract OCR on a file uploaded to S3.
Make sure you have:
1. A file uploaded to S3 (PDF or image)
2. AWS credentials configured in .env
3. Textract permissions enabled
"""

from src.aws_textract import TextractClient
from src.aws_s3 import S3Client
from botocore.exceptions import ClientError
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_textract_ocr():
    """Test Textract OCR on a file in S3."""
    print("🔍 Testing Amazon Textract OCR...")
    print("=" * 50)
    
    # Get configuration
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not bucket_name:
        print("❌ AWS_S3_BUCKET_NAME not set in .env")
        sys.exit(1)
    
    print(f"📦 Bucket: {bucket_name}")
    print(f"🌍 Region: {region}")
    print()
    
    # Initialize clients
    try:
        s3_client = S3Client(bucket_name=bucket_name)
        textract_client = TextractClient(region_name=region)
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        sys.exit(1)
    
    # Check if bucket has any files
    print("📋 Checking for files in S3 bucket...")
    # Note: We'd need list_objects_v2 for this, but for now just prompt user
    
    # Get file from user or use a test file
    print("\nTo test Textract, you need a file in S3.")
    print("Options:")
    print("  1. Upload a test PDF/image to S3 first")
    print("  2. Or provide an S3 object key if you already have a file")
    print()
    
    s3_object_key = input("Enter S3 object key (or press Enter to skip): ").strip()
    
    if not s3_object_key:
        print("\n⏭️  Skipping Textract test (no file provided)")
        print("\nTo test manually:")
        print("  1. Upload a PDF/image to your S3 bucket")
        print("  2. Run this script again with the object key")
        return 0
    
    # Test basic text detection
    print(f"\n🔍 Detecting text in: {s3_object_key}")
    try:
        result = textract_client.detect_document_text(bucket_name, s3_object_key)
        
        print("\n✅ Text detection successful!")
        print(f"📄 Full text ({len(result['text'])} chars):")
        print("-" * 50)
        print(result['text'][:500])  # First 500 chars
        if len(result['text']) > 500:
            print("... (truncated)")
        print("-" * 50)
        
        print(f"\n📊 Statistics:")
        print(f"  - Lines detected: {len(result['lines'])}")
        print(f"  - Words detected: {len(result['words'])}")
        print(f"  - Blocks: {len(result['blocks'])}")
        
        # Test room label extraction
        print(f"\n🏠 Extracting room labels...")
        labels = textract_client.extract_room_labels(bucket_name, s3_object_key)
        
        if labels:
            print(f"✅ Found {len(labels)} potential room labels:")
            for label in labels:
                print(f"  - {label['text']} (confidence: {label['confidence']:.1f}%)")
        else:
            print("  No room labels detected")
        
        print("\n✅ Textract test complete!")
        return 0
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"\n❌ Textract error: {error_code}")
        print(f"   {error_message}")
        print("\nTroubleshooting:")
        print("  - Verify file exists in S3")
        print("  - Check IAM permissions for Textract")
        print("  - Ensure file format is supported (PDF, PNG, JPG)")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_textract_ocr())

