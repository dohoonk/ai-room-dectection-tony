"""
Image preprocessing module for raster blueprint processing.

Handles grayscale conversion, noise reduction, and contrast enhancement
to prepare images for edge and line detection.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class PreprocessingConfig:
    """Configuration for image preprocessing."""
    gaussian_blur_kernel_size: int = 5
    gaussian_blur_sigma: float = 1.0
    use_histogram_equalization: bool = True
    use_adaptive_equalization: bool = False  # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: Tuple[int, int] = (8, 8)


class ImagePreprocessor:
    """Preprocessor for blueprint images."""
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Initialize image preprocessor.
        
        Args:
            config: Preprocessing configuration. If None, uses defaults.
        """
        self.config = config or PreprocessingConfig()
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline to an image.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale if needed
        gray = self.to_grayscale(image)
        
        # Apply noise reduction
        denoised = self.reduce_noise(gray)
        
        # Enhance contrast
        enhanced = self.enhance_contrast(denoised)
        
        return enhanced
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale.
        
        Args:
            image: Input image (BGR, RGB, or already grayscale)
            
        Returns:
            Grayscale image
        """
        if len(image.shape) == 2:
            # Already grayscale
            return image.copy()
        elif len(image.shape) == 3:
            # Color image - convert to grayscale
            if image.shape[2] == 3:
                # BGR or RGB
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif image.shape[2] == 4:
                # BGRA or RGBA
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                raise ValueError(f"Unsupported image format: {image.shape}")
        else:
            raise ValueError(f"Invalid image shape: {image.shape}")
    
    def reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Gaussian blur to reduce noise.
        
        Args:
            image: Grayscale image
            
        Returns:
            Denoised image
        """
        kernel_size = self.config.gaussian_blur_kernel_size
        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        return cv2.GaussianBlur(
            image,
            (kernel_size, kernel_size),
            self.config.gaussian_blur_sigma
        )
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using histogram equalization.
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        if self.config.use_adaptive_equalization:
            # Use CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # Better for images with varying lighting conditions
            clahe = cv2.createCLAHE(
                clipLimit=self.config.clahe_clip_limit,
                tileGridSize=self.config.clahe_tile_grid_size
            )
            return clahe.apply(image)
        elif self.config.use_histogram_equalization:
            # Use standard histogram equalization
            return cv2.equalizeHist(image)
        else:
            # No contrast enhancement
            return image
    
    def get_image_info(self, image: np.ndarray) -> dict:
        """
        Get information about an image.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with image information
        """
        info = {
            'shape': image.shape,
            'dtype': str(image.dtype),
            'min_value': float(image.min()),
            'max_value': float(image.max()),
            'mean_value': float(image.mean()),
            'is_grayscale': len(image.shape) == 2,
        }
        
        if len(image.shape) == 3:
            info['channels'] = image.shape[2]
        else:
            info['channels'] = 1
        
        return info


def preprocess_image(image: np.ndarray, 
                    config: Optional[PreprocessingConfig] = None) -> np.ndarray:
    """
    Convenience function to preprocess an image.
    
    Args:
        image: Input image (BGR, RGB, or grayscale)
        config: Preprocessing configuration. If None, uses defaults.
        
    Returns:
        Preprocessed grayscale image
    """
    preprocessor = ImagePreprocessor(config)
    return preprocessor.preprocess(image)

