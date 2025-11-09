"""
Unit tests for AWS S3 integration.

Note: These tests require AWS credentials and a test bucket.
For CI/CD, use moto (AWS mocking library) or skip tests if credentials not available.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.aws_s3 import S3Client, create_s3_client


class TestS3ClientInitialization:
    """Test cases for S3 client initialization."""
    
    def test_init_with_parameters(self):
        """Test initialization with explicit parameters."""
        with patch('boto3.client') as mock_boto:
            mock_s3 = MagicMock()
            mock_boto.return_value = mock_s3
            
            client = S3Client(
                bucket_name='test-bucket',
                region_name='us-west-2',
                aws_access_key_id='test-key',
                aws_secret_access_key='test-secret'
            )
            
            assert client.bucket_name == 'test-bucket'
            assert client.region_name == 'us-west-2'
            mock_boto.assert_called_once()
    
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch('boto3.client') as mock_boto, \
             patch.dict(os.environ, {
                 'AWS_S3_BUCKET_NAME': 'env-bucket',
                 'AWS_REGION': 'us-east-1',
                 'AWS_ACCESS_KEY_ID': 'env-key',
                 'AWS_SECRET_ACCESS_KEY': 'env-secret'
             }):
            mock_s3 = MagicMock()
            mock_boto.return_value = mock_s3
            
            client = S3Client()
            
            assert client.bucket_name == 'env-bucket'
            assert client.region_name == 'us-east-1'
    
    def test_init_missing_bucket_name(self):
        """Test initialization fails without bucket name."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="S3 bucket name required"):
                S3Client()


class TestS3Upload:
    """Test cases for file upload."""
    
    @patch('boto3.client')
    def test_upload_file_success(self, mock_boto):
        """Test successful file upload."""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        file_content = b'test file content'
        
        object_key = client.upload_file(
            file_content,
            file_name='test.pdf',
            content_type='application/pdf'
        )
        
        assert object_key is not None
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args
        assert call_args[1]['Bucket'] == 'test-bucket'
        assert call_args[1]['Body'] == file_content
    
    @patch('boto3.client')
    def test_upload_file_with_folder(self, mock_boto):
        """Test file upload with folder prefix."""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        file_content = b'test content'
        
        object_key = client.upload_file(
            file_content,
            file_name='test.pdf',
            folder='pdfs/'
        )
        
        assert object_key.startswith('pdfs/')
        mock_s3.put_object.assert_called_once()
    
    @patch('boto3.client')
    def test_upload_file_error(self, mock_boto):
        """Test upload error handling."""
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'PutObject'
        )
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        
        with pytest.raises(ClientError):
            client.upload_file(b'test', file_name='test.pdf')


class TestS3Download:
    """Test cases for file download."""
    
    @patch('boto3.client')
    def test_get_file_success(self, mock_boto):
        """Test successful file download."""
        mock_s3 = MagicMock()
        mock_response = {'Body': MagicMock()}
        mock_response['Body'].read.return_value = b'file content'
        mock_s3.get_object.return_value = mock_response
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        content = client.get_file('test.pdf')
        
        assert content == b'file content'
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test.pdf'
        )
    
    @patch('boto3.client')
    def test_get_file_not_found(self, mock_boto):
        """Test file not found error."""
        mock_s3 = MagicMock()
        mock_s3.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Not found'}},
            'GetObject'
        )
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        
        with pytest.raises(FileNotFoundError):
            client.get_file('nonexistent.pdf')


class TestS3Operations:
    """Test cases for other S3 operations."""
    
    @patch('boto3.client')
    def test_delete_file(self, mock_boto):
        """Test file deletion."""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        result = client.delete_file('test.pdf')
        
        assert result is True
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test.pdf'
        )
    
    @patch('boto3.client')
    def test_file_exists(self, mock_boto):
        """Test file existence check."""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        
        # File exists
        assert client.file_exists('test.pdf') is True
        mock_s3.head_object.assert_called_with(
            Bucket='test-bucket',
            Key='test.pdf'
        )
        
        # File doesn't exist
        mock_s3.head_object.side_effect = ClientError(
            {'Error': {'Code': '404'}},
            'HeadObject'
        )
        assert client.file_exists('nonexistent.pdf') is False
    
    @patch('boto3.client')
    def test_get_file_url(self, mock_boto):
        """Test presigned URL generation."""
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/test-bucket/test.pdf?signature=...'
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        url = client.get_file_url('test.pdf', expires_in=3600)
        
        assert url.startswith('https://')
        mock_s3.generate_presigned_url.assert_called_once()
    
    @patch('boto3.client')
    def test_test_connection_success(self, mock_boto):
        """Test successful connection."""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket')
        success, message = client.test_connection()
        
        assert success is True
        assert 'Successfully connected' in message
    
    @patch('boto3.client')
    def test_test_connection_bucket_not_found(self, mock_boto):
        """Test connection failure - bucket not found."""
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = ClientError(
            {'Error': {'Code': '404'}},
            'HeadBucket'
        )
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='nonexistent-bucket')
        success, message = client.test_connection()
        
        assert success is False
        assert 'Bucket not found' in message


class TestConvenienceFunction:
    """Test cases for convenience function."""
    
    @patch('boto3.client')
    def test_create_s3_client(self, mock_boto):
        """Test convenience function."""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        with patch.dict(os.environ, {'AWS_S3_BUCKET_NAME': 'test-bucket'}):
            client = create_s3_client()
            
            assert isinstance(client, S3Client)
            assert client.bucket_name == 'test-bucket'

