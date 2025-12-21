#!/usr/bin/env python3
"""
Simple wrapper for the vector database builder CLI.

This forwards all commands to the integrated CLI in scripts/
which properly uses the existing infrastructure.

Usage:
    python3 build_vectordb.py --help
    python3 build_vectordb.py build --max-plans 100
    python3 build_vectordb.py status
"""

import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    # Run the actual CLI script
    script_path = Path(__file__).parent / 'scripts' / 'build_vectordb_cli.py'
    
    # Pass all arguments to the CLI script
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    
    sys.exit(subprocess.call(cmd))


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def check_prerequisites():
    """Check if all prerequisites are installed."""
    issues = []
    
    # Check Selenium
    try:
        import selenium
    except ImportError:
        issues.append("Selenium not installed: pip install selenium")
    
    # Check ChromeDriver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options)
        driver.quit()
    except Exception as e:
        issues.append(f"ChromeDriver not available: {e}")
        issues.append("Install with: brew install --cask chromedriver (macOS)")
        issues.append("Or download from: https://chromedriver.chromium.org/")
    
    # Check Gemini
    try:
        import google.generativeai as genai
    except ImportError:
        issues.append("Google GenerativeAI not installed: pip install google-generativeai")
    
    if issues:
        print("⚠️  Prerequisites missing:\n")
        for issue in issues:
            print(f"  • {issue}")
        print()
        return False
    
    print("✅ All prerequisites installed\n")
    return True


def show_current_status():
    """Show current vector DB status."""
    try:
        # Lazy import to avoid circular import issues
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.vectorstore.health_check import VectorDBHealthChecker
        checker = VectorDBHealthChecker()
        result = checker.check_health()
        
        print("📊 Current Vector DB Status:")
        print(f"  Status: {result.status.upper()}")
        print(f"  Regulation count: {result.regulation_count}")
        
        if result.issues:
            print(f"\n  Issues:")
            for issue in result.issues:
                print(f"    • {issue}")
        
        if result.recommendations:
            print(f"\n  Recommendations:")
            for rec in result.recommendations:
                print(f"    • {rec}")
        
        print()
    except Exception as e:
        print(f"⚠️  Could not check vector DB status: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Build the vector database from iPlan/Mavat data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build with first 10 plans (testing)
  python build_vectordb.py --max-plans 10

  # Build with first 100 plans
  python build_vectordb.py --max-plans 100

  # Clear and rebuild entire database
  python build_vectordb.py --rebuild --max-plans 1000

  # Build from TAMA 35 service
  python build_vectordb.py --service tama35 --max-plans 50

  # Check current status
  python build_vectordb.py --status

  # Run with visible browser (debugging)
  python build_vectordb.py --no-headless --max-plans 5

Available services:
  - xplan: Main planning database (default)
  - xplan_full: Full database including sections 77/78
  - tama35: TAMA 35 urban renewal plans
  - tama: National outline plans
        """
    )
    
    # Options
    parser.add_argument(
        '--max-plans',
        type=int,
        default=None,
        help='Maximum number of plans to process (default: all)'
    )
    
    parser.add_argument(
        '--service',
        type=str,
        default='xplan',
        choices=['xplan', 'xplan_full', 'tama35', 'tama'],
        help='iPlan service to use (default: xplan)'
    )
    
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Clear and rebuild the vector database'
    )
    
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Show browser window (useful for debugging)'
    )
    
    parser.add_argument(
        '--no-documents',
        action='store_true',
        help='Skip document fetching (faster, metadata only)'
    )
    
    parser.add_argument(
        '--no-vision',
        action='store_true',
        help='Skip vision processing (faster, no content extraction)'
    )
    
    parser.add_argument(
        '--where',
        type=str,
        default='1=1',
        help='SQL WHERE clause for filtering plans (advanced)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current vector DB status and exit'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check prerequisites and exit'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    print("="*80)
    print("🏗️  Vector Database Builder")
    print("="*80)
    print()
    
    # Handle special commands
    if args.check:
        check_prerequisites()
        return
    
    if args.status:
        show_current_status()
        return
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Please install missing prerequisites before continuing.")
        sys.exit(1)
    
    # Show current status
    show_current_status()
    
    # Confirm rebuild
    if args.rebuild:
        print("⚠️  WARNING: This will clear the existing vector database!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
        print()
    
    # Show configuration
    print("📋 Configuration:")
    print(f"  Service: {args.service}")
    print(f"  Max plans: {args.max_plans or 'all'}")
    print(f"  Rebuild: {args.rebuild}")
    print(f"  Fetch documents: {not args.no_documents}")
    print(f"  Vision processing: {not args.no_vision}")
    print(f"  Headless: {not args.no_headless}")
    if args.where != '1=1':
        print(f"  Filter: {args.where}")
    print()
    
    # Confirm start
    if not args.rebuild:
        response = input("Start building? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
    print()
    
    # Build configuration
    from src.vectorstore.unified_pipeline import build_vectordb, PipelineConfig
    
    config = PipelineConfig(
        service_name=args.service,
        max_plans=args.max_plans,
        where_clause=args.where,
        rebuild_vectordb=args.rebuild,
        fetch_documents=not args.no_documents,
        process_documents=not args.no_vision,
        headless=not args.no_headless,
    )
    
    # Run pipeline
    try:
        print("🚀 Starting pipeline...\n")
        stats = build_vectordb(
            max_plans=args.max_plans,
            service_name=args.service,
            rebuild=args.rebuild,
            headless=not args.no_headless
        )
        
        print("\n" + "="*80)
        print("✅ Vector database build complete!")
        print("="*80)
        print()
        print(f"📊 Results:")
        print(f"  Plans processed: {stats.plans_processed}")
        print(f"  Documents found: {stats.documents_found}")
        print(f"  Regulations indexed: {stats.regulations_indexed}")
        print()
        
        # Show new status
        print("📊 Updated Vector DB Status:")
        show_current_status()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
