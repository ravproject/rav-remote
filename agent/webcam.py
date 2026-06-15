"""
Module for webcam intrusion capture.
"""
import cv2
from loguru import logger
from typing import Optional

def capture_webcam() -> Optional[bytes]:
    """
    Capture a single frame from the default webcam.
    Returns JPEG bytes.
    """
    try:
        # 0 is usually the default built-in webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logger.error("Webcam not accessible.")
            return None
            
        # Give camera a moment to adjust lighting (warm-up)
        # Reading multiple frames is better than just sleeping
        for _ in range(10):
            cap.read()
        
        # Read final frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            logger.error("Failed to read frame from webcam.")
            return None
            
        # Encode as JPEG
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            logger.error("Failed to encode webcam frame.")
            return None
            
        return encoded_image.tobytes()
        
    except Exception as e:
        logger.error(f"Webcam capture failed: {e}")
        return None
