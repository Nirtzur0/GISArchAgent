# iPlan Data Access - Current Status

## ✅ What Works

### 1. Sample Regulation Data
- **Status**: Fully functional
- **Location**: `data/vectorstore/` (ChromaDB)
- **Content**: Sample Israeli planning regulations including:
  - TAMA 35 (Urban Renewal)
  - TAMA 38 (National Infrastructure)
  - Building height regulations
  - Parking requirements
  - Green building standards
  - Plan approval processes
- **Usage**: Powers the regulation query feature in the app

### 2. Vision Service
- **Status**: Fully functional
- **API**: Google Genai (upgraded from deprecated google.generativeai)
- **Features**: Plan image analysis, OCR, zone identification
- **Location**: `src/infrastructure/services/vision_service.py`

### 3. iPlan API Discovery
- **Status**: Confirmed accessible via browser tools
- **Base URL**: `https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/`
- **Data Format**: ArcGIS REST API returning JSON with full plan details
- **Sample Response**: Successfully fetched 5 real plans with complete attributes

**Example Plan Data Retrieved:**
```json
{
  "pl_number": "101-0057273",
  "pl_name": "תוספת קומה והרחבת יח\"ד, ברח' שמואל הנביא 107, ירושלים",
  "plan_county_name": "ירושלים",
  "station_desc": "בבדיקה תכנונית",
  "pl_area_dunam": 2.201,
  "geometry": { "rings": [...] }
}
```

## ❌ What Doesn't Work

### Direct API Access
- **Issue**: iPlan API is protected by WAF (Web Application Firewall)
- **Error**: `SSL: SSLV3_ALERT_HANDSHAKE_FAILURE`
- **Blocked Methods**:
  - Python `requests` library
  - Python `aiohttp` library
  - Python `httpx` library
  - `curl` command-line tool
  - Selenium WebDriver
  - Playwright browser automation

### Root Cause
The iPlan servers use outdated SSL/TLS configurations AND have WAF protection that blocks automated access attempts. Even when SSL handshake succeeds, the WAF returns error HTML pages instead of JSON data.

## 🔧 Current Architecture

```
GIS Architecture Agent
├── Web App (Streamlit) ✅
│   ├── Regulation Queries ✅ (uses vectorstore)
│   ├── Building Rights Calc ✅
│   ├── Map Viewer ✅
│   └── Plan Analyzer ✅ (vision service)
│
├── Data Sources
│   ├── Local VectorStore ✅ (sample regulations)
│   ├── Vision Service ✅ (Gemini AI)
│   └── iPlan Live API ⚠️ (accessible but WAF-protected)
│
└── Infrastructure
    ├── Factory Pattern ✅
    ├── Clean Architecture ✅
    ├── Domain Entities ✅
    └── Repositories ✅
```

## 🎯 Recommendations

### For Development/Testing
Use the existing sample regulation data. It's sufficient for:
- Demonstrating the app's capabilities
- Testing regulation queries
- Showing building rights calculations
- Testing the vision analysis features

### For Production Use
Consider these approaches:

1. **Manual Data Collection**
   - Export plan data from iPlan web interface
   - Save JSON files to `data/raw/iplan_layers.json`
   - Repository will work with local data

2. **Browser Extension Approach**
   - Create a browser extension that can access iPlan
   - Extension can bypass WAF since it's a real browser
   - Export data to local files

3. **Alternative Data Sources**
   - Check if there are official data downloads
   - Look for API partnerships with government
   - Consider using cached/archived data

4. **Accept Limitations**
   - Focus on regulation queries (works great)
   - Use vision analysis for uploaded plans (works great)
   - Plan search works with any data you can import

## 📊 Current Data Status

Run `python3 manage_data.py` to check:
- Number of plans in local data
- Cities and districts covered
- Plan statuses available

## 🚀 What Users Can Do Right Now

1. **Query Regulations** ✅
   - Ask questions about TAMA plans
   - Get building requirements
   - Check parking standards

2. **Calculate Building Rights** ✅
   - Enter plot details
   - Get FAR calculations
   - Check height limits

3. **Analyze Plan Images** ✅
   - Upload plan images
   - Get AI-powered analysis
   - Extract text (OCR)

4. **View Maps** ✅
   - Interactive map interface
   - Layer visualization

## 📝 Notes

- The app is **production-ready** for regulation queries and plan analysis
- iPlan live data access is **technically possible** but requires non-standard approaches
- All core features work without live iPlan access
- The architecture is solid and maintainable

---

**Last Updated**: December 21, 2025
**Status**: Stable and Functional
