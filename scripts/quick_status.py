#!/usr/bin/env python3
"""
Quick status check for vector database without circular imports.

Simple standalone script that checks the vector DB status.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_vectordb_status():
    """Check vector DB status without full imports."""
    import chromadb
    from pathlib import Path
    
    db_path = Path("data/vectorstore")
    metadata_file = db_path / "metadata.json"
    
    print("📊 Vector Database Status")
    print("=" * 70)
    print()
    
    # Check if database exists
    chroma_db = db_path / "chroma.sqlite3"
    if not chroma_db.exists():
        print("  Status: UNINITIALIZED")
        print("  ⚠️  Vector database not found")
        print()
        print("  Run: python3 scripts/build_vectordb_cli.py build --max-plans 10")
        return
    
    # Try to connect and count
    try:
        client = chromadb.PersistentClient(path=str(db_path))
        
        # Get collections
        collections = client.list_collections()
        
        if not collections:
            print("  Status: EMPTY")
            print("  📭 No collections found")
            return
        
        # Count regulations
        reg_count = 0
        for collection in collections:
            if 'regulation' in collection.name.lower():
                try:
                    reg_count = collection.count()
                    break
                except:
                    pass
        
        print(f"  Status: {'HEALTHY' if reg_count >= 100 else 'WARNING' if reg_count >= 10 else 'LOW'}")
        print(f"  Regulation count: {reg_count}")
        print()
        
        if reg_count < 10:
            print("  Issues:")
            print("    • Very low regulation count")
            print()
            print("  Recommendations:")
            print("    • Run: python3 scripts/build_vectordb_cli.py build --max-plans 100")
        elif reg_count < 100:
            print("  Recommendations:")
            print("    • Consider building more data (currently < 100 regulations)")
            print("    • Run: python3 scripts/build_vectordb_cli.py build --max-plans 1000")
        else:
            print("  ✅ Database looks healthy!")
        
        print()
        
        # Check metadata
        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
                last_updated = metadata.get('last_updated')
                if last_updated:
                    print(f"  Last updated: {last_updated}")
        
    except Exception as e:
        print(f"  ⚠️  Error checking database: {e}")


if __name__ == '__main__':
    check_vectordb_status()
