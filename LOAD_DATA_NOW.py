#!/usr/bin/env python3
"""
SUPER SIMPLE data loader - minimal dependencies.
This should work even if other things fail.
"""

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 LOADING DATA - Super Simple Version")
    print("="*70 + "\n")

    import sys
    from pathlib import Path

    # Add project to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    try:
        # Step 1: Load sample data file
        print("📂 Step 1: Loading sample data file...")
        import json

        sample_file = project_root / "data" / "samples" / "iplan_sample_data.json"
        print(f"   Reading: {sample_file}")

        with open(sample_file) as f:
            data = json.load(f)

        features = data.get('features', [])
        print(f"   ✅ Found {len(features)} plans\n")

        # Step 2: Import required classes
        print("📦 Step 2: Importing dependencies...")
        from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
        from src.domain.entities.regulation import Regulation, RegulationType
        from datetime import datetime
        print("   ✅ Imports successful\n")

        # Step 3: Initialize repository
        print("🗄️  Step 3: Connecting to vector database...")
        repo = ChromaRegulationRepository()
        print("   ✅ Connected\n")

        # Step 4: Convert and save
        print("💾 Step 4: Converting and saving regulations...")
        regulations = []

        for i, feat in enumerate(features, 1):
            attrs = feat.get('attributes', {})

            reg = Regulation(
                id=str(attrs.get('objectid', i)),
                title=attrs.get('pl_name', f"Plan {i}"),
                content=f"Plan: {attrs.get('pl_number')}\nArea: {attrs.get('plan_area_name')}\nType: {attrs.get('entity_subtype_desc')}",
                type=RegulationType.LOCAL_PLAN,
                jurisdiction=attrs.get('plan_area_name', 'Israel'),
                effective_date=datetime.now(),
                metadata={'plan_number': attrs.get('pl_number'), 'source': 'sample'}
            )
            regulations.append(reg)

            if i % 5 == 0:
                print(f"   Processing... {i}/{len(features)}")

        print(f"   ✅ Created {len(regulations)} regulations\n")

        # Step 5: Save to database
        print("💾 Step 5: Saving to vector database...")
        repo.save_batch(regulations)
        print("   ✅ Saved!\n")

        # Step 6: Verify
        print("✅ Step 6: Verifying...")
        stats = repo.get_statistics()
        total = stats.get('total_regulations', 0)
        print(f"   Total regulations in DB: {total}\n")

        # Success!
        print("="*70)
        print("🎉 SUCCESS!")
        print("="*70)
        print(f"\n✅ Loaded {len(regulations)} regulations into the database")
        print(f"✅ Total regulations now: {total}")
        print("\n💡 Next steps:")
        print("   1. Open http://localhost:8501 in your browser")
        print("   2. Go to 'System Stats' to see the data")
        print("   3. Ask questions about Israeli planning regulations!")
        print("\n" + "="*70 + "\n")

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: File not found: {e}")
        print("   Make sure you're running from the project root directory")
        sys.exit(1)

    except ImportError as e:
        print(f"\n❌ ERROR: Import failed: {e}")
        print("   Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

