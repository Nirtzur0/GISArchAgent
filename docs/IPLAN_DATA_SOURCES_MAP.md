# iPlan/Mavat Data Sources - Complete Mapping

## 🗺️ Israeli Planning Data Ecosystem

### 1. **iPlan GIS Services (ArcGIS REST API)**

Base: `https://ags.iplan.gov.il/arcgis/rest/services/`

#### Available Services:
1. **PlanningPublic/Xplan** - Main planning database
   - Endpoint: `/PlanningPublic/Xplan/MapServer/0`
   - Data: Current plans, detailed plans, outline plans
   - Fields: ~50+ attributes per plan

2. **PlanningPublic/xplan_without_77_78** - Filtered version
   - Endpoint: `/PlanningPublic/xplan_without_77_78/MapServer/1`
   - Data: Plans excluding sections 77/78
   - Currently used in our codebase

3. **PlanningPublic/Tama35** - TAMA 35 plans
   - Endpoint: `/PlanningPublic/Tama35/MapServer/0`
   - Data: Urban renewal plans under TAMA 35

4. **PlanningPublic/Tama** - General TAMA plans
   - Endpoint: `/PlanningPublic/Tama/MapServer/0`
   - Data: National outline plans

5. **Additional Layers** (Need to map):
   - Building permits
   - Zoning maps
   - Land use designations
   - Conservation areas
   - Infrastructure plans

### 2. **Mavat Portal (Planning Documents)**

Base: `https://mavat.iplan.gov.il/`

#### Document Types:
1. **Plan Sheets** (תשריטים)
   - Format: PDF, DWG, Image files
   - URL pattern: `/SV4/1/{plan_id}/310`
   - Content: Visual planning documents, maps

2. **Regulations** (תקנון)
   - Format: PDF, DOC
   - Content: Legal regulations text
   - Hebrew + some English

3. **Approval Documents** (מסמכי אישור)
   - Format: PDF
   - Content: Official approval letters, committee decisions

4. **Announcements** (הודעות)
   - Format: PDF
   - Content: Public notices, objections period

5. **Protocols** (פרוטוקולים)
   - Format: PDF
   - Content: Committee meeting minutes

### 3. **iPlan Web Portal** (www.iplan.gov.il)

#### Interactive Features:
1. **Plan Search**
   - Search by number, location, status
   - Filter options
   - Export capabilities

2. **Map Viewer**
   - Interactive GIS viewer
   - Layer toggling
   - Spatial queries

3. **Plan Status Tracking**
   - Timeline view
   - Status updates
   - Process stages

### 4. **Related Databases**

#### Ministry of Interior APIs:
1. **Building Permit Database**
   - Endpoint: TBD (need to research)
   - Data: Individual building permits

2. **Land Registry Integration**
   - Cross-reference with Tabu data
   - Property boundaries

3. **Municipal GIS Systems**
   - Tel Aviv GIS
   - Jerusalem GIS
   - Haifa GIS
   - Each municipality has own system

---

## 🚧 Current Problems

### SSL/WAF Issues:
1. **Direct API Access**: ❌ Blocked with 302 redirect to error page
2. **Python requests**: ❌ WAF detects and blocks
3. **curl**: ❌ Same WAF blocking
4. **Browser access**: ✅ Works (JavaScript challenges?)

### Root Causes:
- WAF (Web Application Firewall) protects API
- Requires browser-like headers/cookies
- Possible JavaScript challenge
- Rate limiting
- Bot detection

---

## 💡 Innovative Solutions

### Option 1: **Selenium/Playwright Automation** (RECOMMENDED)
```python
# Use real browser to bypass WAF
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')

driver = webdriver.Chrome(options=options)
driver.get(API_URL)
data = driver.find_element_by_tag_name('pre').text
```

**Pros:**
- ✅ Bypasses WAF (real browser)
- ✅ Handles JavaScript challenges
- ✅ Can interact with UI
- ✅ Can download documents from Mavat

**Cons:**
- ⚠️ Slower than direct API
- ⚠️ More resource intensive
- ⚠️ Requires ChromeDriver/GeckoDriver

### Option 2: **HTTP Session with Browser Headers**
```python
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.iplan.gov.il/',
    'Origin': 'https://www.iplan.gov.il',
    'DNT': '1',
    'Connection': 'keep-alive',
})

# May need to solve CAPTCHA/challenge first
response = session.get(API_URL)
```

**Pros:**
- ✅ Faster than browser automation
- ✅ Less resource intensive

**Cons:**
- ⚠️ May still be blocked
- ⚠️ Needs cookie/session management
- ⚠️ WAF may detect pattern

### Option 3: **Official API Access** (Best Long-term)
```python
# Contact Ministry of Interior for API key
API_KEY = "official_key"
headers = {'Authorization': f'Bearer {API_KEY}'}
```

**Pros:**
- ✅ No WAF issues
- ✅ Official support
- ✅ Reliable
- ✅ Higher rate limits

**Cons:**
- ⚠️ Requires approval process
- ⚠️ May take time to obtain
- ⚠️ May have usage restrictions

### Option 4: **Hybrid Approach** (RECOMMENDED FOR NOW)
```python
# 1. Map all available data with Selenium
# 2. Cache structure/metadata
# 3. Use direct API where possible
# 4. Fall back to Selenium for blocked requests
# 5. Use Gemini vision for document analysis
```

**Strategy:**
1. **Discovery Phase** (One-time):
   - Use Selenium to map all available services
   - Document all endpoints and parameters
   - Download service metadata
   - Cache structure

2. **Regular Fetching**:
   - Try direct API first
   - If blocked → Use Selenium
   - Cache aggressively
   - Respect rate limits

3. **Document Processing**:
   - Selenium for Mavat document links
   - Download PDFs/DWGs
   - Use vision service to analyze
   - Index extracted content

---

## 📋 Data Structure Mapping

### Plan Object (Complete Schema):
```json
{
  "objectid": 123,
  "pl_number": "101-0121850",
  "pl_name": "שינוי קו בניין...",
  "pl_id": 1000210583,
  "district_name": "ירושלים",
  "plan_area_name": "ירושלים",
  "plan_county_name": "ירושלים",
  "entity_subtype_desc": "תכנית מתאר מקומית",
  "plan_charactor_name": "תכנית שמכוחה ניתן להוציא היתרים",
  "station_desc": "בבדיקה תכנונית",
  "pl_area_dunam": 0.066,
  "pl_url": "https://mavat.iplan.gov.il/SV4/1/1000210583/310",
  "pl_objectives": "שינוי קו בנין...",
  "last_update_date": 1543881600000,
  "geometry": {
    "rings": [[...]]
  }
}
```

### Regulation Object (To Extract):
```json
{
  "id": "reg_101_0121850",
  "plan_id": "iplan_1000210583",
  "type": "building_line",
  "title": "Building Line Modification",
  "content": "Full regulation text...",
  "zone_type": "residential",
  "building_rights": {
    "max_floors": 4,
    "max_coverage": 40,
    "far": 1.2,
    "setback": 3.0
  },
  "location": "Jerusalem",
  "source": "mavat_document",
  "document_url": "https://mavat.iplan.gov.il/..."
}
```

---

## 🎯 Unified Data Pipeline Architecture

### Phase 1: Discovery & Mapping
```
Selenium Browser → Map ALL Services
                 ↓
        Discover All Plans
                 ↓
        Cache Plan Metadata
                 ↓
        Index Plan IDs
```

### Phase 2: Data Fetching
```
For Each Plan:
  1. Fetch plan details (Selenium)
  2. Get Mavat URL
  3. Navigate to Mavat page
  4. Extract document links
  5. Download documents
  6. Cache everything
```

### Phase 3: Document Processing
```
For Each Document:
  1. Convert PDF to images
  2. Run vision analysis (Gemini)
  3. Extract regulations
  4. Parse building rights
  5. Extract Hebrew text (OCR)
```

### Phase 4: Vector DB Indexing
```
For Each Regulation:
  1. Create regulation entity
  2. Generate embeddings
  3. Add to ChromaDB
  4. Update metadata
```

---

## 🔧 Implementation Plan

### Week 1: Selenium Infrastructure
- [ ] Set up Selenium with headless Chrome
- [ ] Create robust browser automation
- [ ] Handle WAF challenges
- [ ] Implement retry logic
- [ ] Add rate limiting

### Week 2: Complete Service Mapping
- [ ] Map all ArcGIS services
- [ ] Document all parameters
- [ ] Test all endpoints with Selenium
- [ ] Cache service metadata
- [ ] Create service registry

### Week 3: Document Fetching
- [ ] Automate Mavat navigation
- [ ] Extract document links
- [ ] Download PDFs/DWGs
- [ ] Implement caching
- [ ] Handle errors gracefully

### Week 4: Unified Pipeline
- [ ] Integrate all components
- [ ] Build unified pipeline
- [ ] Add progress tracking
- [ ] Implement checkpointing
- [ ] Add recovery mechanisms

---

## 📊 Expected Data Volume

### Plans:
- Total: ~500,000+ plans nationwide
- Active: ~50,000
- Target for MVP: 1,000 plans

### Documents per Plan (Average):
- Plan sheets: 2-5 PDFs
- Regulations: 1-2 PDFs
- Approvals: 1-3 PDFs
- Total docs: 4-10 per plan

### Vector DB Size (1,000 plans):
- Regulations extracted: ~5,000-10,000
- Total embeddings: ~10,000
- Storage: ~500MB-1GB

---

## ✨ Key Innovation: Smart Caching Strategy

```python
# Three-tier caching
1. API Response Cache (7 days)
   - Raw API responses
   - Fast re-indexing

2. Document Cache (30 days)
   - Downloaded PDFs/DWGs
   - Avoid re-downloads

3. Analysis Cache (90 days)
   - Vision analysis results
   - Expensive to regenerate
   - Update only when needed
```

This mapping provides the foundation for building a robust, scalable data pipeline that can handle the complexity of the Israeli planning system.
