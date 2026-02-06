#!/usr/bin/env python3
"""
Simple script to load iPlan data using the working data sources.
This bypasses the complex unified pipeline and uses the simpler approach.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("🗄️  Loading iPlan Data - Simple Approach")
    print("=" * 70)
    print()

    try:
        # Use the data sources directly
        from src.data_pipeline.sources import IPlanDataSource
        from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository

        print("📦 Initializing data source...")
        source = IPlanDataSource()

        print("📦 Initializing vector database...")
        repo = ChromaRegulationRepository()

        print()
        print("🔍 Discovering plans from iPlan (max 1000)...")

        # Fetch plans using the data source
        plans = source.fetch(max_records=1000)

        print(f"✅ Found {len(plans)} plans")
        print()

        if not plans:
            print("❌ No plans found. The cache might be empty.")
            print()
            print("Try running the discovery first:")
            print("  python3 -c \"from src.data_pipeline.sources import IPlanDataSource; s = IPlanDataSource(); s.fetch(max_records=1000)\"")
            return

        print("📝 Sample plans:")
        for plan in plans[:3]:
            print(f"  - {plan.get('plan_number', 'Unknown')}: {plan.get('plan_name', 'Unknown')[:50]}...")
        print()

        print("💾 Converting plans to regulations for vector DB...")
        from src.domain.entities.regulation import Regulation, RegulationType
        from datetime import datetime

        regulations = []
        for idx, plan in enumerate(plans):
            try:
                # Create a regulation from plan data
                reg = Regulation(
                    id=str(plan.get('objectid', idx)),
                    title=plan.get('plan_name', f"Plan {plan.get('plan_number', 'Unknown')}"),
                    content=f"Plan Number: {plan.get('plan_number', 'N/A')}\n"
                            f"Municipality: {plan.get('municipality_name', 'N/A')}\n"
                            f"Type: {plan.get('entity_subtype', 'N/A')}\n"
                            f"Status: {plan.get('status_description', 'N/A')}\n"
                            f"District: {plan.get('district_name', 'N/A')}",
                    type=RegulationType.LOCAL_PLAN,
                    jurisdiction=plan.get('municipality_name', 'Unknown'),
                    effective_date=datetime.now(),
                    metadata={
                        'plan_number': plan.get('plan_number'),
                        'objectid': plan.get('objectid'),
                        'source': 'iPlan',
                        'district': plan.get('district_name'),
                        'entity_subtype': plan.get('entity_subtype'),
                    }
                )
                regulations.append(reg)
            except Exception as e:
                logger.warning(f"Failed to convert plan {idx}: {e}")
                continue

        print(f"✅ Created {len(regulations)} regulations")
        print()

        print("🗄️  Indexing into vector database...")
        try:
            # Add to vector DB in batches
            batch_size = 100
            for i in range(0, len(regulations), batch_size):
                batch = regulations[i:i+batch_size]
                repo.save_batch(batch)
                print(f"  Indexed {min(i+batch_size, len(regulations))}/{len(regulations)}")

            print()
            print("=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            print()
            print(f"📊 Results:")
            print(f"  Plans fetched: {len(plans)}")
            print(f"  Regulations indexed: {len(regulations)}")
            print()

            # Get stats
            stats = repo.get_statistics()
            print(f"📈 Vector DB Stats:")
            print(f"  Total regulations: {stats.get('total_regulations', 'N/A')}")
            print(f"  Collection: {stats.get('collection_name', 'N/A')}")
            print()

            print("🎉 Data is ready! You can now:")
            print("  1. Open the web app and ask questions")
            print("  2. Check System Stats page to see the data")
            print("  3. Run: python3 scripts/quick_status.py")
            print()

        except Exception as e:
            print(f"❌ Error indexing: {e}")
            logger.exception("Indexing failed")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Failed to load data")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

