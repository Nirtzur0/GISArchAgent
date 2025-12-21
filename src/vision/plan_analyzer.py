"""
Vision Language Model Plan Analyzer
Analyzes architectural plans, maps, and diagrams using VLM with efficient token usage.
"""

import base64
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import io
import json
from datetime import datetime

from PIL import Image
import requests

from src.config import settings

logger = logging.getLogger(__name__)


class PlanVisionAnalyzer:
    """
    Analyzes architectural plans and maps using vision language models.
    
    Features:
    - Intelligent caching to avoid re-analyzing same images
    - Image preprocessing (resize, compress) to reduce tokens
    - OCR extraction before VLM analysis
    - Structured output for efficient querying
    - Support for multiple VLM providers (OpenAI, Google, Anthropic)
    """
    
    def __init__(self, cache_dir: str = "data/vision_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_cache = {}
        self._load_cache_index()
        
    def _load_cache_index(self):
        """Load cached analysis index from disk."""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.analysis_cache = json.load(f)
                logger.info(f"Loaded {len(self.analysis_cache)} cached analyses")
            except Exception as e:
                logger.error(f"Error loading cache index: {e}")
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self.analysis_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")
    
    def _get_image_hash(self, image_data: bytes) -> str:
        """Generate hash for image to use as cache key."""
        return hashlib.sha256(image_data).hexdigest()
    
    def _preprocess_image(
        self, 
        image: Image.Image, 
        max_size: tuple = (1024, 1024),
        quality: int = 85
    ) -> tuple[Image.Image, int]:
        """
        Preprocess image to reduce token usage.
        
        Args:
            image: PIL Image
            max_size: Maximum dimensions (width, height)
            quality: JPEG quality (1-100)
        
        Returns:
            Tuple of (processed_image, estimated_tokens)
        """
        # Resize if too large
        if image.width > max_size[0] or image.height > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized image to {image.size}")
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Estimate tokens (rough approximation: 85 tokens per 512x512 tile)
        tiles_width = (image.width + 511) // 512
        tiles_height = (image.height + 511) // 512
        estimated_tokens = 85 * tiles_width * tiles_height + 170  # Base tokens
        
        return image, estimated_tokens
    
    def _encode_image(self, image: Image.Image) -> str:
        """Encode image as base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _extract_text_ocr(self, image: Image.Image) -> Optional[str]:
        """
        Extract text from image using OCR as first pass.
        This reduces need for VLM if plan has readable text.
        """
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
            if text.strip():
                logger.info(f"OCR extracted {len(text)} characters")
                return text.strip()
        except ImportError:
            logger.warning("pytesseract not installed, skipping OCR")
        except Exception as e:
            logger.error(f"OCR failed: {e}")
        return None
    
    def analyze_plan_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        question: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze an architectural plan image using VLM.
        
        Args:
            image_path: Path to local image file
            image_url: URL to image
            image_bytes: Raw image bytes
            question: Specific question about the image
            use_cache: Whether to use cached analysis
        
        Returns:
            Dictionary with analysis results
        """
        # Load image
        if image_path:
            with open(image_path, 'rb') as f:
                image_data = f.read()
        elif image_url:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content
        elif image_bytes:
            image_data = image_bytes
        else:
            raise ValueError("Must provide image_path, image_url, or image_bytes")
        
        # Check cache
        image_hash = self._get_image_hash(image_data)
        cache_key = f"{image_hash}_{question}" if question else image_hash
        
        if use_cache and cache_key in self.analysis_cache:
            logger.info(f"Using cached analysis for {cache_key}")
            return self.analysis_cache[cache_key]
        
        # Open and preprocess image
        image = Image.open(io.BytesIO(image_data))
        processed_image, estimated_tokens = self._preprocess_image(image)
        
        logger.info(f"Analyzing image (estimated {estimated_tokens} tokens)")
        
        # Try OCR first for text extraction
        ocr_text = self._extract_text_ocr(processed_image)
        
        # Build analysis prompt
        if question:
            prompt = f"Answer this question about the architectural plan: {question}"
        else:
            prompt = self._get_default_analysis_prompt()
        
        # If OCR found substantial text, include it to reduce VLM token usage
        if ocr_text and len(ocr_text) > 100:
            prompt += f"\n\nText extracted from plan:\n{ocr_text[:500]}..."
        
        # Analyze with VLM
        analysis = self._analyze_with_vlm(processed_image, prompt)
        
        # Add metadata
        result = {
            'analysis': analysis,
            'ocr_text': ocr_text,
            'estimated_tokens': estimated_tokens,
            'image_hash': image_hash,
            'timestamp': datetime.now().isoformat(),
            'question': question
        }
        
        # Cache result
        self.analysis_cache[cache_key] = result
        self._save_cache_index()
        
        return result
    
    def _get_default_analysis_prompt(self) -> str:
        """Get default prompt for general plan analysis."""
        return """Analyze this architectural/planning document and extract:

1. **Document Type**: (e.g., site plan, floor plan, zoning map, elevation)
2. **Key Information**: 
   - Plot/building dimensions
   - Room labels and sizes
   - Setbacks and boundaries
   - North arrow and scale
3. **Zoning/Regulatory Info**:
   - Zone designation
   - Building coverage
   - Floor area ratio
   - Height restrictions
4. **Notable Features**:
   - Special markings or annotations
   - TAMA references
   - Approval stamps or dates
5. **Text Content**: Any Hebrew or English text visible

Provide a structured summary focusing on quantifiable data."""
    
    def _analyze_with_vlm(self, image: Image.Image, prompt: str) -> str:
        """
        Analyze image using the configured vision language model.
        
        Args:
            image: Preprocessed PIL Image
            prompt: Analysis prompt
        
        Returns:
            Analysis text
        """
        # Encode image
        base64_image = self._encode_image(image)
        
        # Use provider based on settings
        if settings.llm_provider == "openai":
            return self._analyze_with_openai(base64_image, prompt)
        elif settings.llm_provider == "google":
            return self._analyze_with_gemini(base64_image, prompt)
        elif settings.llm_provider == "anthropic":
            return self._analyze_with_claude(base64_image, prompt)
        else:
            raise ValueError(f"Unsupported provider: {settings.llm_provider}")
    
    def _analyze_with_openai(self, base64_image: str, prompt: str) -> str:
        """Analyze with OpenAI GPT-4 Vision."""
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Use gpt-4o-mini for cost efficiency (supports vision)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"  # Use low detail to reduce tokens
                            }
                        }
                    ]
                }
            ],
            max_tokens=500  # Limit response length
        )
        
        return response.choices[0].message.content
    
    def _analyze_with_gemini(self, base64_image: str, prompt: str) -> str:
        """Analyze with Google Gemini Vision (cheapest option)."""
        import google.generativeai as genai
        
        genai.configure(api_key=settings.google_api_key)
        
        # Use Gemini Flash for cost efficiency
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convert base64 to PIL Image for Gemini
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        
        response = model.generate_content([prompt, image])
        return response.text
    
    def _analyze_with_claude(self, base64_image: str, prompt: str) -> str:
        """Analyze with Anthropic Claude Vision."""
        from anthropic import Anthropic
        
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        # Use Claude 3 Haiku for cost efficiency
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )
        
        return message.content[0].text
    
    def ask_about_plan(self, image_source: str, question: str) -> str:
        """
        Ask a specific question about a plan image.
        
        Args:
            image_source: Path or URL to image
            question: Question in plain language
        
        Returns:
            Answer text
        """
        # Determine if source is URL or path
        if image_source.startswith('http'):
            result = self.analyze_plan_image(image_url=image_source, question=question)
        else:
            result = self.analyze_plan_image(image_path=image_source, question=question)
        
        return result['analysis']
    
    def batch_analyze_plans(
        self,
        image_sources: List[str],
        shared_question: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple plans efficiently.
        
        Args:
            image_sources: List of image paths/URLs
            shared_question: Optional question to ask about all images
        
        Returns:
            List of analysis results
        """
        results = []
        
        for i, source in enumerate(image_sources):
            logger.info(f"Analyzing plan {i+1}/{len(image_sources)}")
            
            try:
                if source.startswith('http'):
                    result = self.analyze_plan_image(
                        image_url=source,
                        question=shared_question
                    )
                else:
                    result = self.analyze_plan_image(
                        image_path=source,
                        question=shared_question
                    )
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {source}: {e}")
                results.append({'error': str(e), 'source': source})
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the analysis cache."""
        total_analyses = len(self.analysis_cache)
        total_tokens_saved = sum(
            r.get('estimated_tokens', 0) 
            for r in self.analysis_cache.values()
        )
        
        return {
            'total_cached_analyses': total_analyses,
            'estimated_tokens_saved': total_tokens_saved,
            'cache_directory': str(self.cache_dir),
            'cache_size_mb': sum(
                f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file()
            ) / (1024 * 1024)
        }


# Singleton instance
_analyzer_instance = None

def get_vision_analyzer() -> PlanVisionAnalyzer:
    """Get or create the singleton vision analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PlanVisionAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    analyzer = PlanVisionAnalyzer()
    
    # Example: Analyze a plan
    # result = analyzer.analyze_plan_image(image_path="path/to/plan.jpg")
    # print(result['analysis'])
    
    # Example: Ask specific question
    # answer = analyzer.ask_about_plan("path/to/plan.jpg", "What is the plot size?")
    # print(answer)
    
    print("Vision analyzer ready!")
    print(f"Cache stats: {analyzer.get_cache_stats()}")
