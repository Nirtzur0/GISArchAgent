"""
Gemini Vision Service Implementation.

Concrete implementation for analyzing plan images with Gemini AI.
"""

import logging
import hashlib
import base64
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

from src.domain.entities.plan import Plan
from src.domain.entities.analysis import VisionAnalysis

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """
    Service for analyzing plan images using Gemini Flash.
    
    Provides OCR, description generation, and zone identification.
    """
    
    # Image preprocessing settings
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920
    JPEG_QUALITY = 85
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash-8b"):
        """
        Initialize service.
        
        Args:
            api_key: Google AI API key
            model: Gemini model name
        """
        self.api_key = api_key
        self.model_name = model
        
        # Configure API
        self.client = genai.Client(api_key=api_key)
        
        logger.info(f"Gemini vision service initialized: {model}")
    
    def analyze_plan(
        self, 
        plan: Plan, 
        image_bytes: bytes,
        include_ocr: bool = True
    ) -> Optional[VisionAnalysis]:
        """
        Analyze a plan image.
        
        Args:
            plan: Plan entity
            image_bytes: Image data
            include_ocr: Whether to extract text
            
        Returns:
            VisionAnalysis entity or None if failed
        """
        try:
            # Calculate image hash
            image_hash = self._calculate_hash(image_bytes)
            
            # Preprocess image
            processed_image = self._preprocess_image(image_bytes)
            
            # Generate description
            description = self._generate_description(processed_image)
            
            # Extract zones (from description)
            zones = self._extract_zones(description)
            
            # Extract text if requested
            extracted_text = None
            if include_ocr:
                extracted_text = self._extract_text(processed_image)
            
            # Create analysis entity
            return VisionAnalysis(
                plan_id=plan.id,
                image_hash=image_hash,
                description=description,
                zones=zones,
                extracted_text=extracted_text,
                tokens_used=0,  # Placeholder
                analysis_cost=0.0  # Placeholder
            )
        
        except Exception as e:
            logger.error(f"Plan analysis failed: {e}")
            return None
    
    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        Preprocess image for optimal API usage.
        
        - Resize to reasonable dimensions
        - Convert to JPEG
        - Compress
        """
        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > self.MAX_WIDTH or image.height > self.MAX_HEIGHT:
                image.thumbnail((self.MAX_WIDTH, self.MAX_HEIGHT), Image.Resampling.LANCZOS)
            
            # Save as JPEG
            output = BytesIO()
            image.save(output, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
            
            return output.getvalue()
        
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image_bytes
    
    def _generate_description(self, image_bytes: bytes) -> str:
        """Generate description of the plan."""
        try:
            # Prepare prompt
            prompt = """
            Analyze this Israeli urban planning document (תוכנית).
            
            Provide a detailed description in English covering:
            1. Type of plan (detailed plan, outline plan, modification)
            2. Main land uses shown
            3. Key zoning designations
            4. Notable features (roads, open spaces, public buildings)
            5. Approximate scale and area covered
            
            Be specific and factual.
            """
            
            # Convert image to Part
            image = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return "Analysis failed"
    
    def _extract_text(self, image_bytes: bytes) -> Optional[str]:
        """Extract text from the plan (OCR)."""
        try:
            # Prepare prompt
            prompt = """
            Extract ALL text from this document, including:
            - Plan name and number
            - Municipality/city name
            - Dates
            - Table contents
            - Legend text
            - Any Hebrew and English text
            
            Output the extracted text exactly as it appears.
            """
            
            # Convert image to Part
            image = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None
    
    def _extract_zones(self, description: str) -> list:
        """
        Extract zone information from description.
        
        Simple heuristic - looks for zone mentions.
        """
        zones = []
        
        # Common Israeli zoning codes
        zone_keywords = [
            'מגורים', 'מסחר', 'תעסוקה', 'מרכז', 'ציבור',
            'שצ"פ', 'דרך', 'חניה', 'גן', 'ספורט',
            'residential', 'commercial', 'employment', 'public', 'open space'
        ]
        
        for keyword in zone_keywords:
            if keyword in description.lower():
                zones.append(keyword)
        
        return zones
    
    def _calculate_hash(self, data: bytes) -> str:
        """Calculate SHA-256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    def get_model_info(self) -> dict:
        """Get information about the model."""
        return {
            'model': self.model_name,
            'max_width': self.MAX_WIDTH,
            'max_height': self.MAX_HEIGHT,
            'jpeg_quality': self.JPEG_QUALITY
        }
