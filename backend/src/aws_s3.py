"""
AWS S3 integration for file storage.

Handles uploading PDF and image files to S3, which is required for
AWS services (Textract, Rekognition) to access files.
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, BinaryIO, Tuple
import os
from datetime import datetime, timezone
import uuid


class S3Client:
    """Client for interacting with AWS S3."""
    
    def __init__(self,
                 bucket_name: Optional[str] = None,
                 region_name: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: S3 bucket name (defaults to AWS_S3_BUCKET_NAME env var)
            region_name: AWS region (defaults to AWS_REGION env var or 'us-east-1')
            aws_access_key_id: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
        """
        self.bucket_name = bucket_name or os.getenv('AWS_S3_BUCKET_NAME')
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.bucket_name:
            raise ValueError(
                "S3 bucket name required. Set AWS_S3_BUCKET_NAME environment variable "
                "or pass bucket_name parameter."
            )
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region_name,
                aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize S3 client: {str(e)}")
    
    def upload_file(self, 
                   file_content: bytes,
                   file_name: Optional[str] = None,
                   content_type: Optional[str] = None,
                   folder: Optional[str] = None) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_content: File content as bytes
            file_name: Original file name (optional, will generate if not provided)
            content_type: MIME type (e.g., 'application/pdf', 'image/png')
            folder: Optional folder prefix (e.g., 'pdfs/', 'images/')
            
        Returns:
            S3 object key (path) of uploaded file
            
        Raises:
            ClientError: If upload fails
        """
        # Generate object key
        if file_name:
            # Preserve original name but add timestamp for uniqueness
            base_name = os.path.basename(file_name)
            name, ext = os.path.splitext(base_name)
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            object_key = f"{folder or ''}{name}_{timestamp}{ext}" if folder else f"{name}_{timestamp}{ext}"
        else:
            # Generate unique name
            unique_id = str(uuid.uuid4())[:8]
            ext = '.pdf' if content_type == 'application/pdf' else '.png'
            object_key = f"{folder or ''}file_{unique_id}{ext}" if folder else f"file_{unique_id}{ext}"
        
        # Ensure folder ends with /
        if folder and not folder.endswith('/'):
            folder = folder + '/'
            object_key = folder + os.path.basename(object_key) if not object_key.startswith(folder) else object_key
        
        try:
            # Upload file
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                **extra_args
            )
            
            return object_key
            
        except ClientError as e:
            raise ClientError(
                error_response={'Error': {'Code': e.response['Error']['Code'],
                                        'Message': f"Failed to upload file to S3: {e.response['Error']['Message']}"}},
                operation_name='PutObject'
            )
    
    def get_file(self, object_key: str) -> bytes:
        """
        Download a file from S3.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            File content as bytes
            
        Raises:
            ClientError: If download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: {object_key}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            True if successful
            
        Raises:
            ClientError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError as e:
            raise ClientError(
                error_response={'Error': {'Code': e.response['Error']['Code'],
                                        'Message': f"Failed to delete file from S3: {e.response['Error']['Message']}"}},
                operation_name='DeleteObject'
            )
    
    def get_file_url(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for temporary file access.
        
        Args:
            object_key: S3 object key (path)
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise ClientError(
                error_response={'Error': {'Code': e.response['Error']['Code'],
                                        'Message': f"Failed to generate presigned URL: {e.response['Error']['Message']}"}},
                operation_name='GeneratePresignedUrl'
            )
    
    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test S3 connection and bucket access.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Try to list bucket (requires ListBucket permission)
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True, f"✅ Successfully connected to S3 bucket: {self.bucket_name}"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False, f"❌ Bucket not found: {self.bucket_name}"
            elif error_code == '403':
                return False, f"❌ Access denied to bucket: {self.bucket_name}. Check IAM permissions."
            else:
                return False, f"❌ Error connecting to S3: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}"


def create_s3_client(bucket_name: Optional[str] = None) -> S3Client:
    """
    Convenience function to create S3 client with default configuration.
    
    Args:
        bucket_name: Optional bucket name override
        
    Returns:
        S3Client instance
    """
    return S3Client(bucket_name=bucket_name)

