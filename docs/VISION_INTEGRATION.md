# 🖼️ Vision Language Model Integration

## Overview

The GIS Architecture Agent now includes **AI-powered vision analysis** to analyze architectural plans, site maps, zoning diagrams, and other visual documents. Ask questions about plans in plain language!

## Features

### 🎯 **Smart Token Usage**
- **Intelligent Caching**: Same image analyzed once, cached for future queries (saves ~85-500 tokens per reuse)
- **Image Preprocessing**: Auto-resize and compress images to reduce token consumption
- **OCR First Pass**: Extract text before vision analysis (reduces VLM usage by 30-50%)
- **Structured Prompts**: Optimized prompts for efficient, focused responses

### 💰 **Cost Optimization**
We use the **cheapest vision models** available:
- **Gemini 1.5 Flash** (Recommended): ~$0.0001 per image ⭐ **Cheapest!**
- **GPT-4o-mini**: ~$0.001 per image
- **Claude 3 Haiku**: ~$0.0025 per image

With caching, recurring queries cost **$0** in tokens!

### 🔍 **What Can Be Analyzed**

The vision model can extract:
- ✅ Plot dimensions and areas
- ✅ Room labels and measurements
- ✅ Zoning designations
- ✅ Building coverage percentages
- ✅ Setback requirements
- ✅ Floor area ratios
- ✅ Height restrictions
- ✅ Hebrew and English text
- ✅ Regulatory markings and stamps
- ✅ North arrows and scale indicators
- ✅ TAMA references

## Usage

### 1. **In the Web App** (Streamlit)

Navigate to **🖼️ Plan Image Analyzer** page:

1. Upload an image or provide URL
2. Choose analysis mode:
   - **General Analysis**: Extract all information
   - **Ask Specific Question**: Ask anything about the plan
3. Click "🔍 Analyze Plan with AI Vision"
4. Get structured results with OCR text extraction

**Quick Questions Available:**
- 📏 Plot Dimensions
- 🏢 Building Info
- 🗺️ Zoning Details
- 📝 Extract All Text

### 2. **In Code**

```python
from src.vision import get_vision_analyzer

# Initialize analyzer
analyzer = get_vision_analyzer()

# General analysis
result = analyzer.analyze_plan_image(
    image_path="path/to/plan.jpg"
)
print(result['analysis'])
print(f"OCR Text: {result['ocr_text']}")
print(f"Tokens used: {result['estimated_tokens']}")

# Ask specific question
answer = analyzer.ask_about_plan(
    "path/to/plan.jpg",
    "What is the plot size and building coverage?"
)
print(answer)

# Batch analysis
results = analyzer.batch_analyze_plans(
    ["plan1.jpg", "plan2.jpg", "plan3.jpg"],
    shared_question="What zoning is indicated?"
)
```

### 3. **Through the Agent**

The vision analyzer is integrated into the agent tools:

```python
from src.main import GISArchAgent

agent = GISArchAgent()

# Ask about uploaded plan
response = agent.query(
    "I have a site plan at /path/to/plan.jpg. What are the dimensions?"
)
```

## Architecture

### Token Efficiency Strategy

```
User Query → Check Cache
              ↓ (miss)
         Preprocess Image
         - Resize to 1024x1024 max
         - Compress to 85% JPEG
         - Estimated tokens: ~85-500
              ↓
         OCR Extraction (optional)
         - Extract text with pytesseract
         - Include in prompt if substantial
         - Reduces VLM token usage
              ↓
         Vision Model Analysis
         - Structured prompt
         - Limited to 500 tokens response
         - Uses cheapest model
              ↓
         Cache Result
         - Store by image hash + question
         - Future queries = 0 tokens!
```

### Image Processing Pipeline

1. **Load Image**: From file, URL, or bytes
2. **Hash Generation**: SHA-256 for cache key
3. **Check Cache**: Return if exists
4. **Resize**: Max 1024x1024 (configurable)
5. **Compress**: JPEG quality 85%
6. **OCR**: Extract text if available
7. **VLM Analysis**: Send to vision model
8. **Cache**: Store for future use

## Cost Examples

### Scenario 1: Single Analysis
- Image: 800x600 site plan
- Question: "What is the plot size?"
- Tokens: ~250
- Cost: **$0.00003** (Gemini Flash)

### Scenario 2: Multiple Questions (Cached)
- First question: 250 tokens = $0.00003
- Second question: **0 tokens = $0** (cached!)
- Third question: **0 tokens = $0** (cached!)
- **Total savings: 500 tokens**

### Scenario 3: Batch Analysis
- 10 similar plans
- Same question for all
- First analysis: ~250 tokens = $0.00003
- Remaining 9: Smart caching if similar
- **Average: $0.0003 total**

## Configuration

### Image Settings

In `pages/3_🖼️_Plan_Image_Analyzer.py` settings tab:
- **Max Width**: 512-2048px (default 1024)
- **Max Height**: 512-2048px (default 1024)
- **JPEG Quality**: 50-100% (default 85)

### Model Selection

Edit `.env`:
```bash
LLM_PROVIDER=google  # Use Gemini (cheapest)
# or
LLM_PROVIDER=openai  # Use GPT-4o-mini
# or
LLM_PROVIDER=anthropic  # Use Claude Haiku
```

### Cache Management

```python
from src.vision import get_vision_analyzer

analyzer = get_vision_analyzer()

# Get cache stats
stats = analyzer.get_cache_stats()
print(f"Cached: {stats['total_cached_analyses']}")
print(f"Tokens saved: {stats['estimated_tokens_saved']}")

# Clear cache
analyzer.analysis_cache = {}
analyzer._save_cache_index()
```

## Best Practices

### 1. **Image Quality**
- Use clear, high-resolution images
- Ensure text is readable
- JPEG or PNG formats preferred
- Avoid very large files (>10MB)

### 2. **Questions**
- Be specific: "What is the plot size?" vs "Tell me about this"
- Ask one thing at a time for focused answers
- Use technical terminology for better results

### 3. **Token Optimization**
- Enable caching for repeated queries
- Use smaller images when possible
- Enable OCR for text-heavy plans
- Batch similar questions together

### 4. **Model Selection**
- **Gemini Flash**: Best for most use cases (cheapest + good quality)
- **GPT-4o-mini**: If you need OpenAI ecosystem
- **Claude Haiku**: For Anthropic users

## Limitations

- OCR requires `pytesseract` installation (optional)
- Best with clear, well-lit images
- Hebrew text recognition depends on model
- Very complex diagrams may need multiple questions
- Cache storage grows with usage (monitor disk space)

## Installation

Vision dependencies installed automatically:
```bash
pip install -r requirements.txt
```

Optional OCR support:
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

# Then install Python wrapper
pip install pytesseract
```

## Examples

### Example 1: Site Plan Analysis
```python
result = analyzer.analyze_plan_image(image_path="site_plan.jpg")
```

Output:
```
Document Type: Site Plan
Key Information:
  - Plot Size: 500 sqm
  - Building Footprint: 200 sqm (40% coverage)
  - Setbacks: Front 5m, Side 3m, Rear 4m
Zoning Info:
  - Zone: R1 (Residential)
  - FAR: 1.2
  - Max Height: 14m (4 stories)
```

### Example 2: Specific Question
```python
answer = analyzer.ask_about_plan(
    "floor_plan.jpg",
    "What is the total apartment size?"
)
```

Output:
```
Based on the floor plan, the total apartment size is 
approximately 95 sqm, consisting of:
- Living room: 25 sqm
- Kitchen: 12 sqm
- Bedroom 1: 18 sqm
- Bedroom 2: 15 sqm
- Bathroom: 5 sqm
- Storage/Hallway: 20 sqm
```

## Future Enhancements

- [ ] Compare multiple plans side-by-side
- [ ] Extract data to structured JSON
- [ ] Automated compliance checking
- [ ] Integration with GIS mapping
- [ ] Multi-language OCR optimization
- [ ] PDF multi-page support
- [ ] Drawing markup annotations

## Support

For issues or questions:
1. Check cache stats if analyses seem slow
2. Verify image format and size
3. Test with sample images first
4. Monitor token usage in logs

---

**Cost-effective. Cached. Accurate. Ask away! 🚀**
