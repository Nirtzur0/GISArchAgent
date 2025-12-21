"""
Document Service - Fetch and process planning documents from Mavat and other sources.

This service handles:
1. Fetching documents (PDFs, DWGs, images) from Mavat planning portal
2. Converting documents to processable formats
3. Caching downloaded documents
4. Extracting document metadata
"""

import logging
import requests
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class PlanDocument:
    """Represents a planning document."""
    plan_id: str
    document_type: str  # 'pdf', 'dwg', 'image'
    url: str
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    downloaded_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MavatDocumentFetcher:
    """
    Fetches planning documents from Mavat (Israeli planning portal).
    
    Mavat URLs format: https://mavat.iplan.gov.il/SV4/1/{plan_id}/310
    
    Documents are typically found at:
    - Plan sheets (תשריט): Image/PDF files
    - Regulations (תקנון): PDF files
    - Approval documents: PDF files
    """
    
    def __init__(self, cache_dir: str = "data/vision_cache"):
        """
        Initialize document fetcher.
        
        Args:
            cache_dir: Directory to cache downloaded documents
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / "pdfs").mkdir(exist_ok=True)
        (self.cache_dir / "images").mkdir(exist_ok=True)
        (self.cache_dir / "dwgs").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_plan_page_url(self, plan_id: str) -> str:
        """
        Get Mavat plan page URL.
        
        Args:
            plan_id: Plan ID from iPlan (e.g., '1000210583')
            
        Returns:
            Mavat URL for the plan page
        """
        return f"https://mavat.iplan.gov.il/SV4/1/{plan_id}/310"
    
    def fetch_plan_documents(self, plan_id: str, mavat_url: Optional[str] = None) -> List[PlanDocument]:
        """
        Fetch all available documents for a plan from Mavat.
        
        Args:
            plan_id: Plan ID
            mavat_url: Optional direct Mavat URL (from iPlan pl_url field)
            
        Returns:
            List of available documents
        """
        try:
            url = mavat_url or self.get_plan_page_url(plan_id)
            
            logger.info(f"Fetching documents for plan {plan_id} from {url}")
            
            # Note: Mavat requires scraping the page to find document links
            # For now, we return a placeholder structure
            # In production, you would parse the HTML to find download links
            
            documents = []
            
            # Check cache first
            cached_docs = self._get_cached_documents(plan_id)
            if cached_docs:
                logger.info(f"Found {len(cached_docs)} cached documents for plan {plan_id}")
                return cached_docs
            
            # TODO: Implement actual Mavat page scraping
            # The page contains links to:
            # - Plan sheets (תשריטים)
            # - Regulations (תקנון)
            # - Approval documents (מסמכי אישור)
            
            logger.warning(
                f"Document fetching from Mavat requires HTML parsing. "
                f"Visit {url} to manually download documents."
            )
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to fetch documents for plan {plan_id}: {e}")
            return []
    
    def download_document(
        self, 
        document_url: str, 
        plan_id: str,
        doc_type: str = "pdf"
    ) -> Optional[PlanDocument]:
        """
        Download a specific document.
        
        Args:
            document_url: URL to download
            plan_id: Associated plan ID
            doc_type: Document type ('pdf', 'image', 'dwg')
            
        Returns:
            PlanDocument with local path or None if failed
        """
        try:
            # Generate filename from URL hash
            url_hash = hashlib.md5(document_url.encode()).hexdigest()[:12]
            extension = self._get_extension_from_url(document_url, doc_type)
            filename = f"{plan_id}_{url_hash}{extension}"
            
            # Determine subdirectory
            subdir = "pdfs" if doc_type == "pdf" else "images" if doc_type == "image" else "dwgs"
            local_path = self.cache_dir / subdir / filename
            
            # Check if already cached
            if local_path.exists():
                logger.info(f"Document already cached: {local_path}")
                return PlanDocument(
                    plan_id=plan_id,
                    document_type=doc_type,
                    url=document_url,
                    local_path=str(local_path),
                    file_size=local_path.stat().st_size,
                    downloaded_at=datetime.fromtimestamp(local_path.stat().st_mtime)
                )
            
            # Download
            logger.info(f"Downloading document: {document_url}")
            response = self.session.get(document_url, timeout=30)
            response.raise_for_status()
            
            # Save
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            doc = PlanDocument(
                plan_id=plan_id,
                document_type=doc_type,
                url=document_url,
                local_path=str(local_path),
                file_size=len(response.content),
                downloaded_at=datetime.now(),
                metadata={
                    'content_type': response.headers.get('content-type'),
                    'source': 'mavat'
                }
            )
            
            logger.info(f"Document downloaded: {local_path} ({doc.file_size} bytes)")
            return doc
            
        except Exception as e:
            logger.error(f"Failed to download document {document_url}: {e}")
            return None
    
    def _get_cached_documents(self, plan_id: str) -> List[PlanDocument]:
        """Get all cached documents for a plan."""
        documents = []
        
        for subdir, doc_type in [("pdfs", "pdf"), ("images", "image"), ("dwgs", "dwg")]:
            dir_path = self.cache_dir / subdir
            for file_path in dir_path.glob(f"{plan_id}_*"):
                documents.append(PlanDocument(
                    plan_id=plan_id,
                    document_type=doc_type,
                    url="cached",
                    local_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    downloaded_at=datetime.fromtimestamp(file_path.stat().st_mtime)
                ))
        
        return documents
    
    def _get_extension_from_url(self, url: str, doc_type: str) -> str:
        """Determine file extension from URL or doc_type."""
        url_lower = url.lower()
        
        if '.pdf' in url_lower:
            return '.pdf'
        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            for ext in ['.jpg', '.jpeg', '.png', '.gif']:
                if ext in url_lower:
                    return ext
        elif '.dwg' in url_lower:
            return '.dwg'
        
        # Fallback based on doc_type
        return {
            'pdf': '.pdf',
            'image': '.jpg',
            'dwg': '.dwg'
        }.get(doc_type, '.bin')


class DocumentProcessor:
    """
    Process planning documents for vision analysis.
    
    Handles:
    - PDF to image conversion
    - DWG to image conversion (if tools available)
    - Image format normalization
    """
    
    def __init__(self):
        self._pdf_available = self._check_pdf_tools()
        self._dwg_available = self._check_dwg_tools()
    
    def _check_pdf_tools(self) -> bool:
        """Check if PDF processing tools are available."""
        try:
            import fitz  # PyMuPDF
            return True
        except ImportError:
            logger.warning("PyMuPDF not available. Install with: pip install PyMuPDF")
            return False
    
    def _check_dwg_tools(self) -> bool:
        """Check if DWG processing tools are available."""
        # DWG conversion typically requires external tools like:
        # - ODA File Converter
        # - LibreCAD
        # - Teigha libraries
        return False
    
    def convert_to_images(self, document: PlanDocument) -> List[str]:
        """
        Convert document to image files for vision analysis.
        
        Args:
            document: Plan document
            
        Returns:
            List of image file paths
        """
        if document.document_type == "image":
            return [document.local_path]
        
        elif document.document_type == "pdf":
            return self._convert_pdf_to_images(document.local_path)
        
        elif document.document_type == "dwg":
            return self._convert_dwg_to_images(document.local_path)
        
        else:
            logger.warning(f"Unknown document type: {document.document_type}")
            return []
    
    def _convert_pdf_to_images(self, pdf_path: str) -> List[str]:
        """Convert PDF pages to images."""
        if not self._pdf_available:
            logger.error("PDF processing not available")
            return []
        
        try:
            import fitz  # PyMuPDF
            
            pdf_path_obj = Path(pdf_path)
            output_dir = pdf_path_obj.parent / f"{pdf_path_obj.stem}_pages"
            output_dir.mkdir(exist_ok=True)
            
            doc = fitz.open(pdf_path)
            image_paths = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                
                image_path = output_dir / f"page_{page_num + 1}.png"
                pix.save(str(image_path))
                image_paths.append(str(image_path))
            
            doc.close()
            logger.info(f"Converted {len(image_paths)} pages from PDF")
            return image_paths
            
        except Exception as e:
            logger.error(f"Failed to convert PDF {pdf_path}: {e}")
            return []
    
    def _convert_dwg_to_images(self, dwg_path: str) -> List[str]:
        """Convert DWG to images."""
        logger.warning("DWG conversion not implemented. Manual conversion required.")
        # TODO: Implement DWG conversion using external tools
        # Options:
        # 1. ODA File Converter (free) + additional processing
        # 2. LibreCAD command line
        # 3. Cloud conversion service
        return []
