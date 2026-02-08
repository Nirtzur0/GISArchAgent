#!/usr/bin/env python3
"""
Test script to verify Pydoll (CDP browser) setup and iPlan access.

This is a standalone script that doesn't depend on the application code.
"""

import sys
from pathlib import Path

def test_pydoll():
    """Test Pydoll installation and headless Chrome launch."""
    print("🧪 Testing Pydoll + Chrome...")
    try:
        import asyncio
        from pydoll.browser.chromium import Chrome

        async def _run():
            browser = Chrome()
            tab = await browser.start(headless=True)
            await tab.go_to("https://www.google.com", timeout=60)
            # `page_source` is a property; accessing it forces a CDP roundtrip.
            _ = tab.page_source
            await browser.stop()

        asyncio.run(_run())
        print("  ✅ Pydoll working! (Chrome launched and navigated)")
        return True
    except Exception as e:
        print(f"  ❌ Pydoll error: {e}")
        return False


def test_iplan_access():
    """Test iPlan API access via browser session (WAF bypass)."""
    print("\n🧪 Testing iPlan API access...")
    try:
        import asyncio
        import json

        # Test URL - get first 5 plans
        url = 'https://ags.iplan.gov.il/arcgisiplan/rest/services/PlanningPublic/xplan_without_77_78/MapServer/1/query?where=1%3D1&outFields=*&f=json&resultRecordCount=5'
        
        print(f"  Fetching: {url[:80]}...")

        async def _run():
            from pydoll.browser.chromium import Chrome

            browser = Chrome()
            tab = await browser.start(headless=True)
            # Seed origin.
            await tab.go_to("https://ags.iplan.gov.il/", timeout=60)
            resp = await tab.request.get(url)
            await browser.stop()
            return resp.text

        body = asyncio.run(_run())
        data = json.loads(body)

        features = data.get("features", [])
        if features:
            print(f"  ✅ iPlan access successful! Found {len(features)} plans")

            first = (features[0] or {}).get("attributes", {}) or {}
            print(f"\n  Example plan:")
            print(f"    Number: {first.get('pl_number') or first.get('PL_NUMBER')}")
            print(f"    Name: {first.get('pl_name') or first.get('PL_NAME')}")
            print(f"    URL: {first.get('pl_url') or first.get('PL_URL')}")
            return True

        print("  ⚠️  Got response but no features")
        return False
            
    except Exception as e:
        print(f"  ❌ iPlan access error: {e}")
        return False


def test_imports():
    """Test required Python packages."""
    print("\n🧪 Testing Python packages...")
    
    packages = {
        'pydoll': 'pydoll-python',
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
    
    # Test browser
    pydoll_ok = test_pydoll()
    
    # Test iPlan access
    if pydoll_ok:
        iplan_ok = test_iplan_access()
    else:
        iplan_ok = False
    
    # Summary
    print("\n" + "="*70)
    print("📊 Summary")
    print("="*70)
    print(f"  Python packages: {'✅ OK' if imports_ok else '❌ Missing packages'}")
    print(f"  Pydoll/Chrome: {'✅ OK' if pydoll_ok else '❌ Not working'}")
    print(f"  iPlan API access: {'✅ OK' if iplan_ok else '❌ Not working'}")
    print()
    
    if imports_ok and pydoll_ok and iplan_ok:
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
