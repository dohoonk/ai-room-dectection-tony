"""
Unit tests for Amazon Textract integration.

Note: These tests require AWS credentials and a test S3 bucket with files.
For CI/CD, use moto (AWS mocking library) or skip tests if credentials not available.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.aws_textract import TextractClient, create_textract_client


class TestTextractClientInitialization:
    """Test cases for Textract client initialization."""
    
    @patch('boto3.client')
    def test_init_with_parameters(self, mock_boto):
        """Test initialization with explicit parameters."""
        mock_textract = MagicMock()
        mock_boto.return_value = mock_textract
        
        client = TextractClient(
            region_name='us-west-2',
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret'
        )
        
        assert client.region_name == 'us-west-2'
        mock_boto.assert_called_once()
    
    @patch('boto3.client')
    def test_init_with_env_vars(self, mock_boto):
        """Test initialization with environment variables."""
        import os
        with patch.dict(os.environ, {
            'AWS_REGION': 'us-east-1',
            'AWS_ACCESS_KEY_ID': 'env-key',
            'AWS_SECRET_ACCESS_KEY': 'env-secret'
        }):
            mock_textract = MagicMock()
            mock_boto.return_value = mock_textract
            
            client = TextractClient()
            
            assert client.region_name == 'us-east-1'


class TestDetectDocumentText:
    """Test cases for document text detection."""
    
    @patch('boto3.client')
    def test_detect_document_text_success(self, mock_boto):
        """Test successful document text detection."""
        mock_textract = MagicMock()
        mock_response = {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Kitchen',
                    'Confidence': 95.5,
                    'Geometry': {'BoundingBox': {}}
                },
                {
                    'BlockType': 'WORD',
                    'Text': 'Kitchen',
                    'Confidence': 95.5,
                    'Geometry': {'BoundingBox': {}}
                }
            ],
            'DocumentMetadata': {'Pages': 1}
        }
        mock_textract.detect_document_text.return_value = mock_response
        mock_boto.return_value = mock_textract
        
        client = TextractClient()
        result = client.detect_document_text('test-bucket', 'test.pdf')
        
        assert 'text' in result
        assert 'lines' in result
        assert 'words' in result
        assert result['text'] == 'Kitchen'
        assert len(result['lines']) == 1
        mock_textract.detect_document_text.assert_called_once()
    
    @patch('boto3.client')
    def test_detect_document_text_error(self, mock_boto):
        """Test error handling for document text detection."""
        mock_textract = MagicMock()
        mock_textract.detect_document_text.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameterException', 'Message': 'Invalid document'}},
            'DetectDocumentText'
        )
        mock_boto.return_value = mock_textract
        
        client = TextractClient()
        
        with pytest.raises(ClientError):
            client.detect_document_text('test-bucket', 'invalid.pdf')


class TestAnalyzeDocument:
    """Test cases for document analysis."""
    
    @patch('boto3.client')
    def test_analyze_document_success(self, mock_boto):
        """Test successful document analysis."""
        mock_textract = MagicMock()
        mock_response = {
            'Blocks': [
                {
                    'BlockType': 'KEY_VALUE_SET',
                    'EntityTypes': ['KEY'],
                    'Id': 'key-1',
                    'Relationships': [{
                        'Type': 'VALUE',
                        'Ids': ['value-1']
                    }]
                },
                {
                    'BlockType': 'KEY_VALUE_SET',
                    'EntityTypes': ['VALUE'],
                    'Id': 'value-1',
                    'Relationships': [{
                        'Type': 'CHILD',
                        'Ids': ['word-1']
                    }]
                },
                {
                    'BlockType': 'WORD',
                    'Id': 'word-1',
                    'Text': 'Kitchen'
                }
            ],
            'DocumentMetadata': {'Pages': 1}
        }
        mock_textract.analyze_document.return_value = mock_response
        mock_boto.return_value = mock_textract
        
        client = TextractClient()
        result = client.analyze_document('test-bucket', 'test.pdf')
        
        assert 'forms' in result
        assert 'tables' in result
        mock_textract.analyze_document.assert_called_once()


class TestExtractRoomLabels:
    """Test cases for room label extraction."""
    
    @patch('boto3.client')
    def test_extract_room_labels(self, mock_boto):
        """Test room label extraction."""
        mock_textract = MagicMock()
        mock_response = {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Kitchen',
                    'Confidence': 95.5,
                    'Geometry': {'BoundingBox': {}}
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Bedroom',
                    'Confidence': 92.0,
                    'Geometry': {'BoundingBox': {}}
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Some other text',
                    'Confidence': 90.0,
                    'Geometry': {'BoundingBox': {}}
                }
            ],
            'DocumentMetadata': {'Pages': 1}
        }
        mock_textract.detect_document_text.return_value = mock_response
        mock_boto.return_value = mock_textract
        
        client = TextractClient()
        labels = client.extract_room_labels('test-bucket', 'test.pdf')
        
        assert len(labels) >= 2  # Should find Kitchen and Bedroom
        assert any('kitchen' in label['text'].lower() for label in labels)
        assert any('bedroom' in label['text'].lower() for label in labels)


class TestConvenienceFunction:
    """Test cases for convenience function."""
    
    @patch('boto3.client')
    def test_create_textract_client(self, mock_boto):
        """Test convenience function."""
        mock_textract = MagicMock()
        mock_boto.return_value = mock_textract
        
        client = create_textract_client()
        
        assert isinstance(client, TextractClient)

