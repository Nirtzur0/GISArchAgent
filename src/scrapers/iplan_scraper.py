"""iPlan system web scraper for extracting planning regulations and data."""

import asyncio
import logging
from typing import List, Dict, Optional
import ssl
import certifi
from bs4 import BeautifulSoup
import aiohttp
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

logger = logging.getLogger(__name__)


class IPlanScraper:
    """Scraper for the iPlan system to extract planning regulations and data.
    
    Uses multiple strategies to bypass SSL errors:
    1. Custom SSL context with relaxed verification
    2. Fallback to requests library with custom adapters
    3. Real-time querying of ArcGIS REST API instead of full scraping
    """
    
    def __init__(self):
        self.base_url = settings.iplan_base_url
        self.api_url = settings.iplan_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self._ssl_context = self._create_ssl_context()
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create a custom SSL context that handles problematic certificates."""
        # Try multiple SSL context strategies
        try:
            # Strategy 1: Use system certificates with fallback
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        except Exception as e:
            logger.warning(f"SSL context creation failed, using insecure context: {e}")
            # Strategy 2: Completely disable SSL verification (last resort)
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        
    async def __aenter__(self):
        """Async context manager entry."""
        # Create session with custom SSL context and connector
        connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def setup_selenium_driver(self) -> webdriver.Chrome:
        """Set up Selenium WebDriver for dynamic content."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_arcgis_layer_info(self, layer_url: str) -> Dict:
        """Fetch information about an ArcGIS map service layer with retry logic."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            params = {"f": "json"}
            async with self.session.get(layer_url, params=params, ssl=self._ssl_context) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Non-200 status from {layer_url}: {response.status}")
                    return {}
        except aiohttp.ClientSSLError as e:
            logger.warning(f"SSL error from {layer_url}, trying fallback: {e}")
            return self._fetch_with_requests_fallback(layer_url)
        except Exception as e:
            logger.error(f"Error fetching layer info from {layer_url}: {e}")
            return {}
    
    def _fetch_with_requests_fallback(self, url: str) -> Dict:
        """Fallback method using requests library with SSL verification disabled."""
        try:
            params = {"f": "json"}
            response = requests.get(
                url, 
                params=params, 
                verify=False,  # Disable SSL verification
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Fallback fetch also failed for {url}: {e}")
            return {}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def query_arcgis_layer(
        self, 
        layer_url: str, 
        where: str = "1=1",
        return_geometry: bool = False,
        out_fields: str = "*",
        result_offset: int = 0,
        result_record_count: int = 100
    ) -> List[Dict]:
        """Query an ArcGIS layer for features with pagination support."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        query_url = f"{layer_url}/query"
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": str(return_geometry).lower(),
            "resultOffset": result_offset,
            "resultRecordCount": result_record_count,
            "f": "json"
        }
        
        try:
            async with self.session.get(query_url, params=params, ssl=self._ssl_context) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("features", [])
                else:
                    logger.warning(f"Non-200 status from {query_url}: {response.status}")
                    return []
        except aiohttp.ClientSSLError as e:
            logger.warning(f"SSL error querying {query_url}, trying fallback: {e}")
            return self._query_with_requests_fallback(query_url, params)
        except Exception as e:
            logger.error(f"Error querying layer {layer_url}: {e}")
            return []
    
    def _query_with_requests_fallback(self, url: str, params: Dict) -> List[Dict]:
        """Fallback query method using requests library."""
        try:
            response = requests.get(
                url,
                params=params,
                verify=False,
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("features", [])
        except Exception as e:
            logger.error(f"Fallback query also failed for {url}: {e}")
            return []
    
    def scrape_main_page(self) -> Dict[str, List[str]]:
        """Scrape the main iPlan page for layer information and structure."""
        driver = self.setup_selenium_driver()
        layers = {
            "planning_layers": [],
            "tama_plans": [],
            "regional_plans": [],
            "zoning_layers": []
        }
        
        try:
            logger.info(f"Loading {self.base_url}")
            driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Allow time for dynamic content
            asyncio.sleep(3)
            
            # Get page source and parse
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract layer information
            # Note: The actual selectors will need to be adjusted based on the site structure
            layer_elements = soup.find_all('div', class_='layer-item')
            
            for element in layer_elements:
                layer_name = element.get_text(strip=True)
                
                if 'תמ"א' in layer_name or 'TAMA' in layer_name:
                    layers["tama_plans"].append(layer_name)
                elif 'תכנית' in layer_name:
                    layers["planning_layers"].append(layer_name)
                elif 'יעוד' in layer_name:
                    layers["zoning_layers"].append(layer_name)
                else:
                    layers["regional_plans"].append(layer_name)
            
            logger.info(f"Found {sum(len(v) for v in layers.values())} layers")
            
        except Exception as e:
            logger.error(f"Error scraping main page: {e}")
        finally:
            driver.quit()
        
        return layers
    
    async def get_planning_layers(self) -> List[Dict]:
        """Get all available planning layers from the iPlan system."""
        layers = []
        
        # Known layer endpoints from the iPlan system
        layer_services = [
            "xplan_without_77_78/MapServer",
            "Xplan_77_78/MapServer",
            "TAMA_1/MapServer",
            "tma_35_compilation_tasrit_mirkamim/MapServer",
            "tma_70/MapServer",
            "ttl_all_blue_lines/MapServer",
        ]
        
        for service in layer_services:
            url = f"{self.api_url}{service}"
            info = await self.fetch_arcgis_layer_info(url)
            if info:
                layers.append({
                    "name": info.get("mapName", service),
                    "url": url,
                    "description": info.get("description", ""),
                    "layers": info.get("layers", [])
                })
        
        return layers
    
    async def scrape_plan_details(self, plan_id: str) -> Dict:
        """Scrape detailed information about a specific plan."""
        # This would query the specific plan details
        # The implementation depends on how plans are accessed in the system
        logger.info(f"Scraping details for plan: {plan_id}")
        
        # Placeholder for plan detail scraping
        return {
            "plan_id": plan_id,
            "details": "Plan details would be extracted here"
        }


async def main():
    """Example usage of the scraper."""
    async with IPlanScraper() as scraper:
        # Get planning layers
        layers = await scraper.get_planning_layers()
        print(f"Found {len(layers)} layer services")
        
        # Scrape main page
        page_layers = scraper.scrape_main_page()
        print(f"Page layers: {page_layers}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
