# 🔍 Vision-First Plan Search Integration

## Overview

The GIS Architecture Agent now **automatically analyzes plan images** when you search for plans. Vision AI is the primary analysis method, with manual upload as a secondary feature.

## Automatic Vision Analysis (Primary)

### How It Works

When you search for plans, the system automatically:

1. **Fetches plan data** from iPlan ArcGIS services
2. **Retrieves plan map images** via MapServer export endpoints
3. **Analyzes with AI vision models** (Gemini/GPT-4o/Claude)
4. **Returns combined results** with visual analysis included

**Example:**
```
User searches: "Tel Aviv residential plans"
  ↓
System fetches: 3 plans from iPlan
  ↓
System retrieves: Map images for each plan
  ↓
System analyzes: Each map with vision AI
  ↓
User receives:
  - Plan metadata (ID, location, status)
  - Map visualization
  - AI analysis (zones, features, regulations)
  - Extracted text (OCR)
  - Token costs
```

### Using Plan Search

1. Navigate to **🔍 Plan Search** page
2. Choose search method:
   - **By Location**: "Tel Aviv", "Jerusalem", etc.
   - **By Plan ID**: "101-0123456"
   - **By Keyword**: "TAMA 35", "residential"
3. Set max results (1-5 plans)
4. Enable "Include Vision Analysis" (default: ON)
5. Click **Search Plans**

**You get:**
- Full plan details
- Interactive map image
- AI visual analysis automatically
- OCR-extracted text
- Downloadable images
- Follow-up question capability

### Vision Analysis Output

For each plan found:

```
📡 Live Data from iPlan with Visual Analysis:

1. **Plan Name**
   Plan ID: 101-0123456
   Location: Tel Aviv-Yafo
   Status: Approved

   🎨 Visual Analysis:
   This planning map shows a residential development zone with...
   [AI-generated detailed description of zones, features, regulations]

   📝 Text Found: 142 words extracted
   💰 Cost: ~250 tokens

   [Interactive map display]
   [Download button]
   [Ask follow-up questions]
```

## Manual Upload (Secondary)

For your own documents:

1. Navigate to **🖼️ Plan Image Analyzer** page
2. Upload image file, URL, or use samples
3. Choose analysis type
4. Get AI analysis

Use this when:
- You have scanned documents
- Analyzing internal firm plans
- Testing with sample images

## Cost Efficiency

### Token Optimization
- **Intelligent caching**: Same plan analyzed once (saves 85-500 tokens per reuse)
- **Image preprocessing**: Resize to 1024x1024, compress 85%
- **OCR first**: Extract text before vision analysis
- **Batch processing**: Multiple plans efficiently

### Model Costs
- **Gemini 1.5 Flash** (default): ~$0.0001/image ⭐ **Cheapest**
- **GPT-4o-mini**: ~$0.001/image
- **Claude 3 Haiku**: ~$0.0025/image

**With caching, repeat queries = $0!**

### Real Cost Example
Searching 3 plans in Tel Aviv:
- First search: 3 images × 250 tokens = 750 tokens (~$0.0003)
- Second search (cached): **$0**
- Follow-up questions: Uses cached analysis

## Technical Details

### Image Fetching from iPlan

The system uses ArcGIS MapServer export endpoints:

```python
# Automatic process when searching
service_url = "https://ags.iplan.gov.il/.../MapServer"
export_url = f"{service_url}/export"

params = {
    'bbox': 'extent_of_plan',
    'size': '800,600',
    'format': 'png',
    'dpi': 96
}

# Image returned as PNG bytes
# Passed to vision analyzer
# Analysis cached by image hash
```

### Vision Analysis Pipeline

```
Plan Search Query
    ↓
iPlan ArcGIS Query → Plan metadata
    ↓
MapServer Export → Plan image (PNG)
    ↓
Image preprocessing → Resize + compress
    ↓
Cache check → Return if exists
    ↓
OCR extraction → pytesseract (optional)
    ↓
Vision API call → Gemini/GPT-4o/Claude
    ↓
Cache result → Save with SHA-256 hash
    ↓
Return to user → Combined analysis
```

### Integration Points

**In `src/scrapers/realtime_fetcher.py`:**
- `get_plan_with_image(service_key, plan_id)` - Fetches plan + image
- `get_plan_map_image(...)` - Exports map from MapServer
- Handles extent calculation and image export

**In `src/tools/architecture_tools.py`:**
- `search_plans(...)` - Modified with `include_vision_analysis=True`
- Automatically fetches images for found plans
- Triggers vision analysis for each
- Returns combined textual + visual results

**In `pages/4_🔍_Plan_Search.py`:**
- New Streamlit page for plan search
- Interactive image display
- Follow-up question interface
- Download capabilities

## Configuration

### Enable/Disable Vision Analysis

In web app:
```python
# Checkbox on search page
include_analysis = st.checkbox("Include Vision Analysis", value=True)
```

In code:
```python
from src.tools.architecture_tools import ArchitectureTools

tools = ArchitectureTools(vectorstore)
results = tools.search_plans(
    location="Tel Aviv",
    include_vision_analysis=True  # Set to False to skip
)
```

### Choose Vision Provider

In `.env`:
```bash
# Use cheapest (Gemini)
GOOGLE_API_KEY=your_key
LLM_PROVIDER=google

# Or use OpenAI
OPENAI_API_KEY=your_key
LLM_PROVIDER=openai

# Or use Anthropic
ANTHROPIC_API_KEY=your_key
LLM_PROVIDER=anthropic
```

## Best Practices

### When to Use Automatic Vision

✅ **Always use** for:
- Searching plans from iPlan
- Analyzing regulation maps
- Querying TAMA zones
- Location-based plan searches

✅ **Benefits**:
- No manual download needed
- Immediate visual insights
- Cached for future queries
- Integrated with plan metadata

### When to Use Manual Upload

✅ **Use for**:
- Internal firm documents
- Scanned architect drawings
- Photos of physical plans
- Non-iPlan sources

### Performance Tips

1. **Use location search** instead of keywords when possible
   - More accurate plan matching
   - Better image availability

2. **Limit results** to 3-5 plans
   - Faster analysis
   - Lower costs
   - More focused results

3. **Enable caching** (default ON)
   - Instant repeat queries
   - Zero token cost
   - Automatic cleanup

4. **Ask follow-up questions** on analyzed plans
   - Uses same cached image
   - No re-analysis needed
   - Focused AI responses

## Examples

### Example 1: Location Search with Vision

```python
# In web app or via agent
User: "Show me residential plans in Ramat Aviv"

System:
- Searches iPlan for Ramat Aviv
- Finds 3 residential plans
- Fetches map image for each
- Analyzes with Gemini Flash
- Returns results with visual descriptions

Output includes:
- Plan IDs and metadata
- Interactive map displays
- AI analysis of each zone
- Building restrictions noted
- Text extracted from maps
```

### Example 2: Plan ID Search

```python
User: "Analyze plan 101-0654321"

System:
- Fetches specific plan from iPlan
- Exports map image
- Runs vision analysis
- Returns detailed breakdown

AI describes:
- Zoning boundaries
- Building envelopes
- Height restrictions
- Setback requirements
- Land use designations
```

### Example 3: Follow-up Questions

```python
# After initial search
User asks: "What are the height limits in zone A?"

System:
- Uses cached image analysis
- Focuses on height restrictions
- Returns specific answer
- Cost: ~50 tokens (vs 250 initial)
```

## Troubleshooting

### No Image Available
Some plans may not have map images:
- Check plan status (approved plans more likely)
- Try different plan ID format
- Use manual upload if you have the document

### Vision Analysis Failed
If analysis fails:
- Check API key configuration
- Verify API quota/limits
- Try different provider (Gemini → GPT-4o)
- Check image format (should be PNG/JPEG)

### Slow Performance
If searches are slow:
- Reduce max results
- Disable vision analysis temporarily
- Check network connection
- Clear cache if very large

### High Token Usage
To reduce costs:
- Enable caching (should be default)
- Use Gemini Flash provider
- Limit result count
- Ask specific questions instead of general analysis

## API Reference

### search_plans()
```python
def search_plans(
    plan_id: Optional[str] = None,
    location: Optional[str] = None, 
    status: Optional[str] = None,
    include_vision_analysis: bool = True
) -> str:
    """
    Search plans with automatic vision analysis.
    
    Args:
        plan_id: Specific plan identifier
        location: City or region name
        status: Filter by status (approved, pending)
        include_vision_analysis: Auto-analyze images (default: True)
        
    Returns:
        Formatted results with plan data and visual analysis
    """
```

### get_plan_with_image()
```python
def get_plan_with_image(
    service_key: str,
    plan_id: str
) -> Optional[Dict]:
    """
    Fetch plan data with map image from iPlan.
    
    Args:
        service_key: Service identifier ('planning', 'tama_35', etc.)
        plan_id: Plan number or OBJECTID
        
    Returns:
        Dict with:
            - plan_data: Plan attributes
            - geometry: Plan boundaries
            - image_bytes: PNG map image
            - has_image: Boolean flag
    """
```

## Future Enhancements

Planned features:
- [ ] PDF plan extraction and analysis
- [ ] Multi-page plan document support
- [ ] Comparison view (2 plans side-by-side)
- [ ] 3D model generation from plans
- [ ] Historical plan comparison
- [ ] Automatic regulation compliance checking
- [ ] Export analysis to PDF report

## Conclusion

The vision-first approach means **you don't need to manually download and upload plans**. Just search, and the AI automatically analyzes what it finds. This is the fastest, most efficient way to understand planning documents.

For the original vision documentation, see [VISION_INTEGRATION.md](VISION_INTEGRATION.md).
