"""
Reinitialize vector database with 100 real iPlan regulations.
This script clears the existing database and loads fresh data from iPlan API.
"""

import sys
import shutil
from pathlib import Path
from src.infrastructure.factory import ApplicationFactory

def reinitialize_vectordb():
    """Clear and reinitialize vector database with real iPlan data."""
    
    print("\n" + "="*70)
    print("🔄 Reinitializing Vector Database with Real iPlan Data")
    print("="*70 + "\n")
    
    # Path to vector database
    vectordb_path = Path("data/vectorstore")
    
    # Step 1: Remove existing database
    if vectordb_path.exists():
        print("📁 Removing existing vector database...")
        try:
            shutil.rmtree(vectordb_path)
            print("   ✓ Existing database removed")
        except Exception as e:
            print(f"   ✗ Failed to remove database: {e}")
            return False
    else:
        print("📁 No existing database found")
    
    # Step 2: Create factory (this will auto-initialize with new data)
    print("\n📥 Creating new vector database with real iPlan data...")
    try:
        factory = ApplicationFactory()
        repo = factory.get_regulation_repository()
        
        # Check initialization status
        status = factory.get_vectordb_status()
        
        if status.get('initialized'):
            total = status.get('total_regulations', 0)
            print(f"   ✓ Database initialized successfully!")
            print(f"   ✓ Total regulations: {total}")
        else:
            print(f"   ✗ Initialization failed: {status.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Verify data quality
    print("\n🔍 Verifying data quality...")
    try:
        stats = repo.get_statistics()
        total_regs = stats.get('total_regulations', 0)
        
        # Test search for iPlan-specific terms
        test_queries = [
            ('תוספת קומה', 'Addition of floor'),
            ('שינוי קו בנין', 'Building line change'),
            ('מגורים', 'Residential')
        ]
        
        all_passed = True
        for hebrew_query, english_desc in test_queries:
            results = repo.search(hebrew_query, limit=3)
            if results:
                print(f"   ✓ Search '{english_desc}': {len(results)} results")
            else:
                print(f"   ✗ Search '{english_desc}': No results")
                all_passed = False
        
        if all_passed and total_regs >= 10:
            print("\n" + "="*70)
            print("✅ SUCCESS: Vector Database Ready!")
            print("="*70)
            print(f"\n📊 Database Statistics:")
            print(f"   • Collection: {stats.get('collection_name', 'N/A')}")
            print(f"   • Total Regulations: {total_regs}")
            print(f"   • Location: {stats.get('persist_directory', 'N/A')}")
            print(f"\n💡 The database now contains real iPlan regulations!")
            print(f"   You can search for Hebrew terms like: תוספת קומה, שינוי בנין, מגורים")
            print("="*70 + "\n")
            return True
        else:
            print(f"\n⚠️  Warning: Only {total_regs} regulations loaded")
            return False
            
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = reinitialize_vectordb()
    sys.exit(0 if success else 1)
