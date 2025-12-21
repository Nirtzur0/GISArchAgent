#!/usr/bin/env python3
"""
Test script to verify Selenium setup and iPlan access.

This is a standalone script that doesn't depend on the application code.
"""

import sys
from pathlib import Path

def test_selenium():
    """Test Selenium installation and ChromeDriver."""
    print("🧪 Testing Selenium and ChromeDriver...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        
        driver = webdriver.Chrome(options=options)
        driver.get('https://www.google.com')
        title = driver.title
        driver.quit()
        
        print(f"  ✅ Selenium working! (Test page title: {title})")
        return True
    except Exception as e:
        print(f"  ❌ Selenium error: {e}")
        print(f"\n  Install ChromeDriver:")
        print(f"    macOS: brew install --cask chromedriver")
        print(f"    Or download from: https://chromedriver.chromium.org/")
        return False


def test_iplan_access():
    """Test iPlan API access with Selenium."""
    print("\n🧪 Testing iPlan API access...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import json
        import time
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Test URL - get first 5 plans
        url = 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query?where=1%3D1&outFields=*&f=json&resultRecordCount=5'
        
        print(f"  Fetching: {url[:80]}...")
        driver.get(url)
        time.sleep(3)  # Wait for page load
        
        # Try to extract JSON
        try:
            pre = driver.find_element('tag name', 'pre')
            data = json.loads(pre.text)
            
            features = data.get('features', [])
            if features:
                print(f"  ✅ iPlan access successful! Found {len(features)} plans")
                
                # Show first plan
                first = features[0].get('attributes', {})
                print(f"\n  Example plan:")
                print(f"    Number: {first.get('PL_NUMBER')}")
                print(f"    Name: {first.get('PL_NAME')}")
                print(f"    URL: {first.get('pl_url')}")
                
                driver.quit()
                return True
            else:
                print(f"  ⚠️  Got response but no features")
                driver.quit()
                return False
                
        except Exception as e:
            print(f"  ❌ Could not parse response: {e}")
            print(f"  Page source (first 200 chars): {driver.page_source[:200]}")
            driver.quit()
            return False
            
    except Exception as e:
        print(f"  ❌ iPlan access error: {e}")
        return False


def test_imports():
    """Test required Python packages."""
    print("\n🧪 Testing Python packages...")
    
    packages = {
        'selenium': 'selenium',
        'requests': 'requests',
        'google.generativeai': 'google-generativeai',
        'chromadb': 'chromadb',
        'PIL': 'Pillow',
        'pypdf': 'pypdf',
    }
    
    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - Install with: pip install {package}")
            all_ok = False
    
    return all_ok


def main():
    print("="*70)
    print("🔍 Vector Database Builder - Setup Verification")
    print("="*70)
    print()
    
    # Test imports
    imports_ok = test_imports()
    
    # Test Selenium
    selenium_ok = test_selenium()
    
    # Test iPlan access
    if selenium_ok:
        iplan_ok = test_iplan_access()
    else:
        iplan_ok = False
    
    # Summary
    print("\n" + "="*70)
    print("📊 Summary")
    print("="*70)
    print(f"  Python packages: {'✅ OK' if imports_ok else '❌ Missing packages'}")
    print(f"  Selenium/ChromeDriver: {'✅ OK' if selenium_ok else '❌ Not working'}")
    print(f"  iPlan API access: {'✅ OK' if iplan_ok else '❌ Not working'}")
    print()
    
    if imports_ok and selenium_ok and iplan_ok:
        print("✅ All tests passed! You're ready to build the vector database.")
        print()
        print("Next steps:")
        print("  1. Set your Gemini API key:")
        print("     export GEMINI_API_KEY='your_key_here'")
        print()
        print("  2. Run a test build:")
        print("     python3 build_vectordb.py --max-plans 10")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
