# Bypassing SSL Errors for iPlan Data Access

## The Problem

The iPlan ArcGIS server (`ags.iplan.gov.il`) uses outdated SSL/TLS configurations that cause handshake failures with modern Python SSL libraries:
- Error: `SSLV3_ALERT_HANDSHAKE_FAILURE`
- Cause: Server requires older TLS protocols or cipher suites

## Solutions Implemented

### 1. **Real-Time Data Fetcher** (`src/scrapers/realtime_fetcher.py`)
Instead of scraping everything, we query the ArcGIS REST API on-demand:
- ✅ No need to pre-download all data
- ✅ Always gets latest information
- ✅ Supports keyword search, location-based queries, TAMA lookups
- ⚠️ Currently blocked by SSL issues

### 2. **SSL Bypass Strategies** (In Order)
1. **Custom SSL Context** - Relaxed certificate verification
2. **Requests Library** - With `verify=False`
3. **urllib with unverified context** - Most permissive option
4. **Alternative approaches below...**

### 3. **Workaround Options**

#### Option A: Use HTTP Instead of HTTPS (if available)
Some ArcGIS services have HTTP endpoints:
```python
# Replace https:// with http://
url = "http://ags.iplan.gov.il/arcgisiplan/rest/services/..."
```

#### Option B: Use a Proxy Server
Set up a local proxy that handles SSL:
```bash
# Install mitmproxy
pip install mitmproxy

# Run proxy
mitmproxy -p 8080 --ssl-insecure

# Configure Python to use proxy
export HTTP_PROXY="http://localhost:8080"
export HTTPS_PROXY="http://localhost:8080"
```

#### Option C: Use Browser Automation
Selenium with Chrome in insecure mode:
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-insecure-localhost')
driver = webdriver.Chrome(options=options)
```

#### Option D: System-Level OpenSSL Configuration
Add to `/etc/ssl/openssl.cnf` or `~/.openssl.cnf`:
```ini
[system_default_sect]
MinProtocol = TLSv1.0
CipherString = DEFAULT@SECLEVEL=1
```

Then set environment variable:
```bash
export OPENSSL_CONF=~/.openssl.cnf
```

#### Option E: Use External API Gateway
Deploy a serverless function (AWS Lambda, Google Cloud Functions) that acts as a proxy:
- Function runs in environment with relaxed SSL
- Your app calls the function instead of iPlan directly

### 4. **Current Implementation**

The system now works in **hybrid mode**:
1. **Cached Data**: Sample regulations stored in ChromaDB vector database
2. **Real-Time Fallback**: Attempts to fetch live data from iPlan
3. **Graceful Degradation**: Falls back to cached data if real-time fails

When you query:
- 📡 First attempts real-time fetch from iPlan
- 💾 Falls back to vector database if unavailable
- ✅ Always returns results (from cache if needed)

### 5. **Testing the Real-Time Fetcher**

```python
from src.scrapers.realtime_fetcher import IPlanRealtimeFetcher

fetcher = IPlanRealtimeFetcher()

# Search by keyword
results = fetcher.search_by_keyword("TAMA 35")

# Search by location  
results = fetcher.get_plans_by_location("Tel Aviv")

# Get specific TAMA
results = fetcher.get_tama_plans("35")
```

### 6. **Recommendations**

For production use, consider:
1. **Contact iPlan administrators** to update their SSL certificate
2. **Use a dedicated scraping service** (ScraperAPI, Bright Data) that handles SSL
3. **Manual data collection** - Download data periodically and update vector database
4. **Proxy server deployment** - Deploy your own SSL-terminating proxy

### 7. **Alternative Data Sources**

Instead of scraping iPlan directly:
- **Download GIS data** from Israeli government open data portals
- **Use Planning Administration API** (if they provide one)
- **Contact local planning offices** for bulk data access
- **Use cached datasets** and update quarterly

## Current Status

✅ **Working**: Vector database with sample regulations  
✅ **Working**: Query system with cached data  
⚠️ **Partial**: Real-time fetching (blocked by SSL)  
🔄 **Recommended**: Use cached data + periodic manual updates

The system is **fully functional** using cached data. Real-time fetching will work once SSL issues are resolved using one of the methods above.
