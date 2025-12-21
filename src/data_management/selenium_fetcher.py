"""
Selenium-based data fetcher for bypassing WAF protection on iPlan/Mavat.

This replaces the LLM-based fetch_webpage approach with a real browser automation
solution that can bypass WAF protection while being more reliable and maintainable.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SeleniumFetcher:
    """
    Browser automation fetcher that bypasses WAF protection.
    
    Uses Selenium with headless Chrome to fetch data from iPlan/Mavat
    as if it were a real browser, bypassing bot detection and WAF.
    """
    
    def __init__(self, headless: bool = True, cache_dir: Optional[Path] = None):
        """
        Initialize the Selenium fetcher.
        
        Args:
            headless: Run browser in headless mode
            cache_dir: Directory for caching responses
        """
        self.headless = headless
        self.cache_dir = cache_dir or Path("data/cache/selenium")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.driver: Optional[webdriver.Chrome] = None
        self._init_driver()
        
    def _init_driver(self):
        """Initialize Chrome WebDriver with anti-detection options."""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless=new')  # Modern headless mode
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        
        # Browser fingerprinting
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=he-IL,he,en-US,en')
        
        # Preferences
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Disable images for faster loading (optional)
        # prefs = {'profile.managed_default_content_settings.images': 2}
        # options.add_experimental_option('prefs', prefs)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            
            # Execute CDP commands to hide automation
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.info("Install ChromeDriver: brew install --cask chromedriver")
            raise
    
    def fetch_json(self, url: str, use_cache: bool = True, timeout: int = 30) -> Dict[str, Any]:
        """
        Fetch JSON data from a URL using Selenium.
        
        Args:
            url: URL to fetch
            use_cache: Use cached response if available
            timeout: Timeout in seconds
            
        Returns:
            Parsed JSON data
        """
        # Check cache first
        if use_cache:
            cached = self._get_from_cache(url)
            if cached:
                logger.info(f"Using cached response for {url}")
                return cached
        
        try:
            logger.info(f"Fetching {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Additional wait for API responses
            time.sleep(2)
            
            # Try to extract JSON from page
            json_data = self._extract_json_from_page()
            
            # Cache the response
            if json_data:
                self._save_to_cache(url, json_data)
            
            return json_data
            
        except TimeoutException:
            logger.error(f"Timeout fetching {url}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def _extract_json_from_page(self) -> Dict[str, Any]:
        """
        Extract JSON data from the current page.
        
        Handles different page structures:
        1. JSON in <pre> tag (common for APIs)
        2. JSON in page source
        3. JavaScript variable
        """
        try:
            # Method 1: Check for <pre> tag (common for JSON APIs)
            try:
                pre_element = self.driver.find_element(By.TAG_NAME, 'pre')
                json_text = pre_element.text
                return json.loads(json_text)
            except:
                pass
            
            # Method 2: Check page source for JSON
            page_source = self.driver.page_source
            
            # Look for JSON-like structures
            if 'features' in page_source or 'attributes' in page_source:
                # Likely ArcGIS REST API response
                try:
                    # Extract JSON from HTML
                    start = page_source.find('{')
                    end = page_source.rfind('}') + 1
                    if start != -1 and end > start:
                        json_text = page_source[start:end]
                        return json.loads(json_text)
                except:
                    pass
            
            # Method 3: Execute JavaScript to get data
            try:
                json_data = self.driver.execute_script('return document.body.textContent')
                return json.loads(json_data)
            except:
                pass
            
            logger.warning("Could not extract JSON from page")
            return {}
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return {}
    
    def fetch_arcgis_service(
        self, 
        service_url: str,
        where: str = "1=1",
        out_fields: str = "*",
        return_geometry: bool = True,
        result_offset: int = 0,
        result_record_count: int = 1000,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch data from ArcGIS REST API service.
        
        Args:
            service_url: Base service URL
            where: SQL WHERE clause
            out_fields: Fields to return
            return_geometry: Include geometry
            result_offset: Pagination offset
            result_record_count: Records per request
            use_cache: Use cache
            
        Returns:
            ArcGIS service response
        """
        # Build query URL
        params = {
            'where': where,
            'outFields': out_fields,
            'returnGeometry': 'true' if return_geometry else 'false',
            'resultOffset': result_offset,
            'resultRecordCount': result_record_count,
            'f': 'json'
        }
        
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{service_url}/query?{query_params}"
        
        return self.fetch_json(full_url, use_cache=use_cache)
    
    def fetch_all_features(
        self,
        service_url: str,
        where: str = "1=1",
        batch_size: int = 1000,
        max_features: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all features from an ArcGIS service with pagination.
        
        Args:
            service_url: Service URL
            where: WHERE clause
            batch_size: Records per request
            max_features: Maximum features to fetch (None for all)
            
        Returns:
            List of all features
        """
        all_features = []
        offset = 0
        
        while True:
            logger.info(f"Fetching batch at offset {offset}")
            
            response = self.fetch_arcgis_service(
                service_url,
                where=where,
                result_offset=offset,
                result_record_count=batch_size
            )
            
            features = response.get('features', [])
            if not features:
                break
            
            all_features.extend(features)
            logger.info(f"Fetched {len(features)} features, total: {len(all_features)}")
            
            offset += batch_size
            
            # Check if we've exceeded max_features
            if max_features and len(all_features) >= max_features:
                all_features = all_features[:max_features]
                break
            
            # Check if we've reached the end
            if len(features) < batch_size:
                break
            
            # Rate limiting
            time.sleep(1)
        
        logger.info(f"Fetched total of {len(all_features)} features")
        return all_features
    
    def fetch_mavat_page(self, plan_id: str) -> str:
        """
        Fetch a Mavat plan page and extract document links.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Page HTML
        """
        url = f"https://mavat.iplan.gov.il/SV4/1/{plan_id}/310"
        
        try:
            logger.info(f"Fetching Mavat page for plan {plan_id}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Wait for content to appear (adjust selector as needed)
            time.sleep(3)
            
            return self.driver.page_source
            
        except Exception as e:
            logger.error(f"Error fetching Mavat page: {e}")
            raise
    
    def extract_document_links(self, plan_id: str) -> List[Dict[str, str]]:
        """
        Navigate to Mavat page and extract all document download links.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List of documents with URLs and metadata
        """
        html = self.fetch_mavat_page(plan_id)
        
        # Extract links using Selenium's DOM methods
        documents = []
        
        try:
            # Find all document links (adjust selectors based on actual page structure)
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="download"], a[href*=".pdf"], a[href*=".dwg"]')
            
            for link in link_elements:
                url = link.get_attribute('href')
                text = link.text.strip()
                
                if url:
                    documents.append({
                        'url': url,
                        'title': text or 'Untitled',
                        'plan_id': plan_id
                    })
            
            logger.info(f"Extracted {len(documents)} document links for plan {plan_id}")
            
        except Exception as e:
            logger.error(f"Error extracting document links: {e}")
        
        return documents
    
    def _get_from_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached response for URL."""
        cache_file = self.cache_dir / f"{hash(url)}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    def _save_to_cache(self, url: str, data: Dict[str, Any]):
        """Save response to cache."""
        cache_file = self.cache_dir / f"{hash(url)}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class IPlanSeleniumSource:
    """
    Data source for iPlan using Selenium.
    
    Replaces the fetch_webpage approach with browser automation.
    """
    
    SERVICES = {
        'xplan': 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1',
        'xplan_full': 'https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Xplan/MapServer/0',
        'tama35': 'https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Tama35/MapServer/0',
        'tama': 'https://ags.iplan.gov.il/arcgis/rest/services/PlanningPublic/Tama/MapServer/0',
    }
    
    def __init__(self, headless: bool = True):
        """
        Initialize iPlan source.
        
        Args:
            headless: Run browser in headless mode
        """
        self.fetcher = SeleniumFetcher(headless=headless)
    
    def discover_plans(
        self,
        service_name: str = 'xplan',
        max_plans: Optional[int] = None,
        where: str = "1=1"
    ) -> List[Dict[str, Any]]:
        """
        Discover all plans from a service.
        
        Args:
            service_name: Service to query
            max_plans: Maximum plans to fetch
            where: SQL WHERE clause for filtering
            
        Returns:
            List of plan features
        """
        service_url = self.SERVICES.get(service_name)
        if not service_url:
            raise ValueError(f"Unknown service: {service_name}")
        
        return self.fetcher.fetch_all_features(
            service_url,
            where=where,
            max_features=max_plans
        )
    
    def fetch_plan_details(self, plan_id: str, service_name: str = 'xplan') -> Dict[str, Any]:
        """
        Fetch details for a specific plan.
        
        Args:
            plan_id: Plan ID (OBJECTID)
            service_name: Service name
            
        Returns:
            Plan feature
        """
        service_url = self.SERVICES.get(service_name)
        where = f"OBJECTID={plan_id}"
        
        response = self.fetcher.fetch_arcgis_service(service_url, where=where)
        features = response.get('features', [])
        
        if features:
            return features[0]
        
        return {}
    
    def fetch_plan_documents(self, plan_id: str) -> List[Dict[str, str]]:
        """
        Fetch all documents for a plan from Mavat.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List of documents
        """
        return self.fetcher.extract_document_links(plan_id)
    
    def close(self):
        """Close resources."""
        self.fetcher.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Selenium-based iPlan data fetcher...")
    
    with IPlanSeleniumSource(headless=True) as source:
        # Fetch first 10 plans
        print("\n1. Discovering plans...")
        plans = source.discover_plans(max_plans=10)
        print(f"Found {len(plans)} plans")
        
        if plans:
            # Show first plan
            first_plan = plans[0]
            attrs = first_plan.get('attributes', {})
            print(f"\nExample plan:")
            print(f"  ID: {attrs.get('OBJECTID')}")
            print(f"  Number: {attrs.get('PL_NUMBER')}")
            print(f"  Name: {attrs.get('PL_NAME')}")
            print(f"  URL: {attrs.get('pl_url')}")
            
            # Try to fetch documents (if pl_url exists)
            pl_url = attrs.get('pl_url')
            if pl_url and 'mavat.iplan.gov.il' in pl_url:
                # Extract plan ID from URL
                import re
                match = re.search(r'/(\d+)/', pl_url)
                if match:
                    plan_id = match.group(1)
                    print(f"\n2. Fetching documents for plan {plan_id}...")
                    documents = source.fetch_plan_documents(plan_id)
                    print(f"Found {len(documents)} documents")
                    
                    for doc in documents[:3]:  # Show first 3
                        print(f"  - {doc['title']}: {doc['url']}")
    
    print("\n✅ Test complete!")
