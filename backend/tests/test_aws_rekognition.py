"""
Unit tests for Amazon Rekognition integration.

Note: These tests require AWS credentials and a test S3 bucket with files.
For CI/CD, use moto (AWS mocking library) or skip tests if credentials not available.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.aws_rekognition import RekognitionClient, create_rekognition_client


class TestRekognitionClientInitialization:
    """Test cases for Rekognition client initialization."""
    
    @patch('boto3.client')
    def test_init_with_parameters(self, mock_boto):
        """Test initialization with explicit parameters."""
        mock_rekognition = MagicMock()
        mock_boto.return_value = mock_rekognition
        
        client = RekognitionClient(
            region_name='us-west-2',
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret'
        )
        
        assert client.region_name == 'us-west-2'
        mock_boto.assert_called_once()


class TestDetectLabels:
    """Test cases for label detection."""
    
    @patch('boto3.client')
    def test_detect_labels_success(self, mock_boto):
        """Test successful label detection."""
        mock_rekognition = MagicMock()
        mock_response = {
            'Labels': [
                {
                    'Name': 'Door',
                    'Confidence': 95.5,
                    'Instances': [{'BoundingBox': {'Left': 0.1, 'Top': 0.2, 'Width': 0.1, 'Height': 0.2}}]
                },
                {
                    'Name': 'Window',
                    'Confidence': 92.0,
                    'Instances': []
                },
                {
                    'Name': 'Building',
                    'Confidence': 98.0,
                    'Instances': []
                }
            ],
            'LabelCount': 3,
            'ImageProperties': {}
        }
        mock_rekognition.detect_labels.return_value = mock_response
        mock_boto.return_value = mock_rekognition
        
        client = RekognitionClient()
        result = client.detect_labels('test-bucket', 'test.jpg')
        
        assert 'labels' in result
        assert 'architectural_elements' in result
        assert len(result['architectural_elements']) >= 2  # Door and Window
        mock_rekognition.detect_labels.assert_called_once()
    
    @patch('boto3.client')
    def test_detect_labels_error(self, mock_boto):
        """Test error handling for label detection."""
        mock_rekognition = MagicMock()
        mock_rekognition.detect_labels.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameterException', 'Message': 'Invalid image'}},
            'DetectLabels'
        )
        mock_boto.return_value = mock_rekognition
        
        client = RekognitionClient()
        
        with pytest.raises(ClientError):
            client.detect_labels('test-bucket', 'invalid.jpg')


class TestDetectText:
    """Test cases for text detection."""
    
    @patch('boto3.client')
    def test_detect_text_success(self, mock_boto):
        """Test successful text detection."""
        mock_rekognition = MagicMock()
        mock_response = {
            'TextDetections': [
                {
                    'DetectedText': 'Kitchen',
                    'Type': 'LINE',
                    'Confidence': 95.5
                },
                {
                    'DetectedText': 'Kitchen',
                    'Type': 'WORD',
                    'Confidence': 95.5
                }
            ]
        }
        mock_rekognition.detect_text.return_value = mock_response
        mock_boto.return_value = mock_rekognition
        
        client = RekognitionClient()
        result = client.detect_text('test-bucket', 'test.jpg')
        
        assert 'text' in result
        assert 'lines' in result
        assert result['text'] == 'Kitchen'
        mock_rekognition.detect_text.assert_called_once()


class TestFilterArchitecturalElements:
    """Test cases for architectural element filtering."""
    
    def test_filter_architectural_elements(self):
        """Test filtering of architectural elements."""
        labels = [
            {'Name': 'Door', 'Confidence': 95.0, 'Categories': [], 'Instances': []},
            {'Name': 'Window', 'Confidence': 92.0, 'Categories': [], 'Instances': []},
            {'Name': 'Sky', 'Confidence': 98.0, 'Categories': [], 'Instances': []},
            {'Name': 'Furniture', 'Confidence': 85.0, 'Categories': [], 'Instances': []}
        ]
        
        client = RekognitionClient.__new__(RekognitionClient)  # Create without init
        elements = client._filter_architectural_elements(labels)
        
        assert len(elements) == 3  # Door, Window, Furniture (not Sky)
        assert any(e['name'] == 'Door' for e in elements)
        assert any(e['name'] == 'Window' for e in elements)
        assert any(e['name'] == 'Furniture' for e in elements)


class TestBoundingBoxIntersection:
    """Test cases for bounding box intersection."""
    
    def test_bounding_boxes_intersect(self):
        """Test bounding box intersection detection."""
        client = RekognitionClient.__new__(RekognitionClient)
        
        # Overlapping boxes
        bbox1 = {'Left': 0.1, 'Top': 0.1, 'Width': 0.2, 'Height': 0.2}
        bbox2 = {'Left': 0.2, 'Top': 0.2, 'Width': 0.2, 'Height': 0.2}
        assert client._bounding_boxes_intersect(bbox1, bbox2) == True
        
        # Non-overlapping boxes
        bbox3 = {'Left': 0.1, 'Top': 0.1, 'Width': 0.1, 'Height': 0.1}
        bbox4 = {'Left': 0.5, 'Top': 0.5, 'Width': 0.1, 'Height': 0.1}
        assert client._bounding_boxes_intersect(bbox3, bbox4) == False


class TestConvenienceFunction:
    """Test cases for convenience function."""
    
    @patch('boto3.client')
    def test_create_rekognition_client(self, mock_boto):
        """Test convenience function."""
        mock_rekognition = MagicMock()
        mock_boto.return_value = mock_rekognition
        
        client = create_rekognition_client()
        
        assert isinstance(client, RekognitionClient)

