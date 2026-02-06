"""
Plan Upload Service - Handle user-uploaded plans and analyze them.

This service provides:
1. Upload validation and processing
2. Vision analysis of uploaded plans
3. Semantic search against existing regulations
4. Building rights extraction
5. Matching similar plans
"""

import logging
from typing import Optional, List, Dict, Any, BinaryIO
from dataclasses import dataclass
from pathlib import Path
import tempfile
from datetime import datetime

from src.domain.entities.analysis import VisionAnalysis
from src.domain.entities.regulation import Regulation
from src.domain.entities.plan import Plan
from src.infrastructure.services.vision_service import GeminiVisionService
from src.infrastructure.services.document_service import DocumentProcessor
from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository

logger = logging.getLogger(__name__)


@dataclass
class UploadedPlanAnalysis:
    """Results from analyzing an uploaded plan."""
    
    # Vision analysis
    vision_analysis: VisionAnalysis
    
    # Semantic search results
    matching_regulations: List[Regulation]
    similarity_scores: List[float]
    
    # Plan classification
    estimated_zone_type: Optional[str] = None
    estimated_location: Optional[str] = None
    
    # Extracted information
    extracted_text: Optional[str] = None
    identified_zones: List[str] = None
    
    # Metadata
    upload_timestamp: datetime = None
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.identified_zones is None:
            self.identified_zones = []
        if self.upload_timestamp is None:
            self.upload_timestamp = datetime.now()


class PlanUploadService:
    """
    Service for handling uploaded planning documents.
    
    Workflow:
    1. Validate uploaded file (format, size)
    2. Convert to processable format (PDF → images)
    3. Run vision analysis (OCR, description, zones)
    4. Extract searchable text
    5. Semantic search against regulations
    6. Return comprehensive analysis
    """
    
    SUPPORTED_FORMATS = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'tiff': 'image/tiff'
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def __init__(
        self,
        vision_service: GeminiVisionService,
        regulation_repo: ChromaRegulationRepository,
        cache_dir: str = "data/vision_cache/uploads"
    ):
        """
        Initialize upload service.
        
        Args:
            vision_service: Vision analysis service
            regulation_repo: Regulation repository for semantic search
            cache_dir: Directory to cache uploaded files
        """
        self.vision_service = vision_service
        self.regulation_repo = regulation_repo
        self.document_processor = DocumentProcessor()
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_uploaded_plan(
        self,
        file_data: BinaryIO,
        filename: str,
        max_results: int = 5
    ) -> Optional[UploadedPlanAnalysis]:
        """
        Analyze an uploaded plan file.
        
        Args:
            file_data: Binary file data
            filename: Original filename
            max_results: Maximum matching regulations to return
            
        Returns:
            Analysis results or None if processing failed
        """
        start_time = datetime.now()
        
        try:
            # Validate file
            if not self._validate_file(file_data, filename):
                return None
            
            # Save to temporary location
            file_path = self._save_upload(file_data, filename)
            
            # Process based on file type
            file_ext = Path(filename).suffix.lower().lstrip('.')
            
            if file_ext == 'pdf':
                # Convert PDF to images
                image_paths = self.document_processor.convert_to_images(
                    type('obj', (object,), {
                        'document_type': 'pdf',
                        'local_path': str(file_path)
                    })()
                )
                
                if not image_paths:
                    logger.error("Failed to convert PDF to images")
                    return None
                
                # Analyze first page (or combine multiple pages)
                analysis_path = image_paths[0]
            else:
                # Direct image analysis
                analysis_path = str(file_path)
            
            # Run vision analysis
            logger.info(f"Running vision analysis on {analysis_path}")
            plan_id = f"upload:{start_time.strftime('%Y%m%d_%H%M%S')}:{Path(filename).name}"
            with open(analysis_path, "rb") as f:
                image_bytes = f.read()
            vision_analysis = self.vision_service.analyze_plan(
                plan_id=plan_id,
                image_bytes=image_bytes,
                include_ocr=True,
            )
            
            if not vision_analysis:
                logger.error("Vision analysis failed")
                return None
            
            # Extract searchable text
            search_text = self._build_search_query(vision_analysis)
            
            # Semantic search for matching regulations
            logger.info(f"Searching for regulations matching: {search_text[:100]}...")
            matches = self.regulation_repo.search_by_text(query=search_text, limit=max_results)
            
            # Extract regulations and scores
            matching_regulations = [m['regulation'] for m in matches]
            similarity_scores = [m['similarity'] for m in matches]
            
            # Classify plan
            estimated_zone = self._estimate_zone_type(vision_analysis)
            estimated_location = self._estimate_location(vision_analysis)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return UploadedPlanAnalysis(
                vision_analysis=vision_analysis,
                matching_regulations=matching_regulations,
                similarity_scores=similarity_scores,
                estimated_zone_type=estimated_zone,
                estimated_location=estimated_location,
                extracted_text=vision_analysis.ocr_text,
                identified_zones=vision_analysis.zones_identified,
                upload_timestamp=start_time,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze uploaded plan: {e}")
            return None
    
    def _validate_file(self, file_data: BinaryIO, filename: str) -> bool:
        """Validate uploaded file."""
        # Check file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in self.SUPPORTED_FORMATS:
            logger.error(f"Unsupported file format: {file_ext}")
            return False
        
        # Check file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset
        
        if file_size > self.MAX_FILE_SIZE:
            logger.error(f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})")
            return False
        
        if file_size == 0:
            logger.error("Empty file")
            return False
        
        return True
    
    def _save_upload(self, file_data: BinaryIO, filename: str) -> Path:
        """Save uploaded file to cache."""
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(filename).name  # Remove any directory components
        saved_filename = f"{timestamp}_{safe_filename}"
        
        file_path = self.cache_dir / saved_filename
        
        # Save
        with open(file_path, 'wb') as f:
            f.write(file_data.read())
        
        logger.info(f"Saved upload: {file_path}")
        return file_path
    
    def _build_search_query(self, vision_analysis: VisionAnalysis) -> str:
        """
        Build semantic search query from vision analysis.
        
        Combines:
        - AI-generated description
        - Extracted text
        - Identified zones
        """
        query_parts = []
        
        if vision_analysis.description:
            query_parts.append(vision_analysis.description)
        
        if vision_analysis.text_content:
            # Take first 200 words of extracted text
            words = vision_analysis.text_content.split()[:200]
            query_parts.append(' '.join(words))
        
        if vision_analysis.zones:
            zones_text = ' '.join(vision_analysis.zones)
            query_parts.append(f"Zones: {zones_text}")
        
        return ' '.join(query_parts)
    
    def _estimate_zone_type(self, vision_analysis: VisionAnalysis) -> Optional[str]:
        """Estimate zone type from vision analysis."""
        description_lower = vision_analysis.description.lower() if vision_analysis.description else ""
        
        # Simple keyword matching
        zone_keywords = {
            'residential': ['residential', 'housing', 'apartments', 'dwelling', 'מגורים'],
            'commercial': ['commercial', 'retail', 'shopping', 'מסחרי'],
            'industrial': ['industrial', 'factory', 'manufacturing', 'תעשיה'],
            'mixed': ['mixed-use', 'mixed use', 'שימוש מעורב'],
            'agricultural': ['agricultural', 'farm', 'חקלאי'],
            'public': ['public', 'institutional', 'ציבורי']
        }
        
        for zone_type, keywords in zone_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return zone_type
        
        return None
    
    def _estimate_location(self, vision_analysis: VisionAnalysis) -> Optional[str]:
        """Estimate location from extracted text."""
        if not vision_analysis.text_content:
            return None
        
        # Look for common Israeli city names
        cities = [
            'ירושלים', 'תל אביב', 'חיפה', 'באר שבע', 'ראשון לציון',
            'פתח תקווה', 'נתניה', 'חדרה', 'רמת גן', 'בני ברק',
            'Jerusalem', 'Tel Aviv', 'Haifa', 'Beer Sheva'
        ]
        
        text = vision_analysis.text_content
        for city in cities:
            if city in text:
                return city
        
        return None
