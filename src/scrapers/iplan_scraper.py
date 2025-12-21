"""iPlan system web scraper for extracting planning regulations and data."""

import asyncio
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from src.config import settings

logger = logging.getLogger(__name__)


class IPlanScraper:
    """Scraper for the iPlan system to extract planning regulations and data."""
    
    def __init__(self):
        self.base_url = settings.iplan_base_url
        self.api_url = settings.iplan_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
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
    
    async def fetch_arcgis_layer_info(self, layer_url: str) -> Dict:
        """Fetch information about an ArcGIS map service layer."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            params = {"f": "json"}
            async with self.session.get(layer_url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching layer info from {layer_url}: {e}")
            return {}
    
    async def query_arcgis_layer(
        self, 
        layer_url: str, 
        where: str = "1=1",
        return_geometry: bool = False,
        out_fields: str = "*"
    ) -> List[Dict]:
        """Query an ArcGIS layer for features."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        query_url = f"{layer_url}/query"
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": str(return_geometry).lower(),
            "f": "json"
        }
        
        try:
            async with self.session.get(query_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("features", [])
        except Exception as e:
            logger.error(f"Error querying layer {layer_url}: {e}")
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
