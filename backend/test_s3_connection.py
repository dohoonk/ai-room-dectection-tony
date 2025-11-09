"""
Test script for S3 connection.

Run this after completing AWS Console setup to verify S3 access.
"""

from src.aws_s3 import S3Client
import os
import sys

def main():
    """Test S3 connection."""
    print("🔍 Testing S3 Connection...")
    print("=" * 50)
    
    # Check environment variables
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not bucket_name:
        print("❌ AWS_S3_BUCKET_NAME environment variable not set")
        print("   Please set it in .env file or environment")
        sys.exit(1)
    
    if not access_key or not secret_key:
        print("⚠️  AWS credentials not found in environment")
        print("   Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set")
        print("   They should be in .env file or .cursor/mcp.json")
    
    print(f"📦 Bucket: {bucket_name}")
    print(f"🌍 Region: {region}")
    print()
    
    try:
        client = S3Client(bucket_name=bucket_name)
        success, message = client.test_connection()
        
        print(message)
        print()
        
        if success:
            print("✅ S3 setup complete! Ready to use.")
            print()
            print("Next steps:")
            print("  1. Test file upload (will be implemented next)")
            print("  2. Integrate with PDF processing pipeline")
            return 0
        else:
            print("❌ Please check your AWS configuration:")
            print("  - Verify bucket name is correct")
            print("  - Check IAM user permissions")
            print("  - Ensure credentials are valid")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure you've completed Steps 1-6 in AWS_S3_SETUP_GUIDE.md")
        print("  2. Verify environment variables are set correctly")
        print("  3. Check AWS credentials are valid")
        return 1

if __name__ == "__main__":
    sys.exit(main())

