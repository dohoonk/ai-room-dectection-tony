"""
Line detection module for raster blueprint processing.

Uses Canny edge detection and Hough line transforms to detect wall lines
in blueprint images.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class EdgeDetectionConfig:
    """Configuration for Canny edge detection."""
    low_threshold: int = 50
    high_threshold: int = 150
    aperture_size: int = 3  # Must be 3, 5, or 7
    l2_gradient: bool = False


@dataclass
class LineDetectionConfig:
    """Configuration for Hough line detection."""
    rho: float = 1.0  # Distance resolution in pixels
    theta: float = np.pi / 180  # Angular resolution in radians
    threshold: int = 100  # Minimum votes for a line
    min_line_length: float = 50.0  # Minimum line length in pixels
    max_line_gap: float = 10.0  # Maximum gap between line segments to connect


@dataclass
class LineDetectionParams:
    """Complete configuration for line detection."""
    edge_config: EdgeDetectionConfig = None
    line_config: LineDetectionConfig = None
    
    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.edge_config is None:
            self.edge_config = EdgeDetectionConfig()
        if self.line_config is None:
            self.line_config = LineDetectionConfig()


class LineDetector:
    """Detector for wall lines in blueprint images."""
    
    def __init__(self, params: Optional[LineDetectionParams] = None):
        """
        Initialize line detector.
        
        Args:
            params: Line detection parameters. If None, uses defaults.
        """
        self.params = params or LineDetectionParams()
    
    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Canny edge detection to detect edges in the image.
        
        Args:
            image: Preprocessed grayscale image
            
        Returns:
            Binary edge image (edges are white, background is black)
        """
        config = self.params.edge_config
        
        # Ensure aperture size is valid (3, 5, or 7)
        aperture = config.aperture_size
        if aperture not in [3, 5, 7]:
            # Round to nearest valid value
            if aperture < 3:
                aperture = 3
            elif aperture > 7:
                aperture = 7
            else:
                aperture = 5
        
        return cv2.Canny(
            image,
            config.low_threshold,
            config.high_threshold,
            apertureSize=aperture,
            L2gradient=config.l2_gradient
        )
    
    def detect_lines(self, edges: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """
        Detect lines using Probabilistic Hough Line Transform.
        
        Args:
            edges: Binary edge image from Canny edge detection
            
        Returns:
            List of lines, each as (x1, y1, x2, y2) tuple
        """
        config = self.params.line_config
        
        # Use Probabilistic Hough Line Transform
        # Returns list of line endpoints: [(x1, y1, x2, y2), ...]
        lines = cv2.HoughLinesP(
            edges,
            rho=config.rho,
            theta=config.theta,
            threshold=config.threshold,
            minLineLength=config.min_line_length,
            maxLineGap=config.max_line_gap
        )
        
        if lines is None:
            return []
        
        # Convert from numpy array to list of tuples
        result = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            result.append((float(x1), float(y1), float(x2), float(y2)))
        
        return result
    
    def detect_lines_from_image(self, image: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """
        Complete pipeline: detect edges then lines from preprocessed image.
        
        Args:
            image: Preprocessed grayscale image
            
        Returns:
            List of lines, each as (x1, y1, x2, y2) tuple
        """
        edges = self.detect_edges(image)
        lines = self.detect_lines(edges)
        return lines
    
    def get_edge_statistics(self, edges: np.ndarray) -> dict:
        """
        Get statistics about detected edges.
        
        Args:
            edges: Binary edge image
            
        Returns:
            Dictionary with edge statistics
        """
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_density = edge_pixels / total_pixels if total_pixels > 0 else 0.0
        
        return {
            'edge_pixel_count': int(edge_pixels),
            'total_pixels': int(total_pixels),
            'edge_density': float(edge_density),
            'image_shape': edges.shape
        }
    
    def get_line_statistics(self, lines: List[Tuple[float, float, float, float]]) -> dict:
        """
        Get statistics about detected lines.
        
        Args:
            lines: List of lines as (x1, y1, x2, y2) tuples
            
        Returns:
            Dictionary with line statistics
        """
        if not lines:
            return {
                'line_count': 0,
                'total_length': 0.0,
                'avg_length': 0.0,
                'min_length': 0.0,
                'max_length': 0.0
            }
        
        lengths = []
        for x1, y1, x2, y2 in lines:
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            lengths.append(length)
        
        return {
            'line_count': len(lines),
            'total_length': float(sum(lengths)),
            'avg_length': float(np.mean(lengths)),
            'min_length': float(min(lengths)),
            'max_length': float(max(lengths))
        }


def detect_lines_from_image(image: np.ndarray,
                           params: Optional[LineDetectionParams] = None) -> List[Tuple[float, float, float, float]]:
    """
    Convenience function to detect lines from a preprocessed image.
    
    Args:
        image: Preprocessed grayscale image
        params: Line detection parameters. If None, uses defaults.
        
    Returns:
        List of lines, each as (x1, y1, x2, y2) tuple
    """
    detector = LineDetector(params)
    return detector.detect_lines_from_image(image)

