t#!/usr/bin/env python3
"""
Load sample data into vector database - guaranteed to work!
Uses the existing sample data file.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
from datetime import datetime

def main():
    print("=" * 70)
    print("🗄️  Loading Sample iPlan Data")
    print("=" * 70)
    print()

    # Load sample data
    data_file = Path("data/samples/iplan_sample_data.json")
    if not data_file.exists():
        print(f"❌ Sample data file not found: {data_file}")
        return 1

    print(f"📂 Loading data from {data_file}...")
    with open(data_file) as f:
        data = json.load(f)

    features = data.get('features', [])
    print(f"✅ Loaded {len(features)} sample plans")
    print()

    if not features:
        print("❌ No features found in sample data")
        return 1

    # Show samples
    print("📝 Sample plans:")
    for feat in features[:3]:
        attrs = feat.get('attributes', {})
        print(f"  - {attrs.get('pl_number')}: {attrs.get('pl_name', '')[:50]}...")
    print()

    # Initialize vector DB
    print("🗄️  Initializing vector database...")
    from src.infrastructure.repositories.chroma_repository import ChromaRegulationRepository
    from src.domain.entities.regulation import Regulation, RegulationType

    repo = ChromaRegulationRepository()

    # Convert to regulations
    print("💾 Converting plans to regulations...")
    regulations = []

    for feat in features:
        attrs = feat.get('attributes', {})

        try:
            reg = Regulation(
                id=str(attrs.get('objectid', attrs.get('pl_id', len(regulations)))),
                title=attrs.get('pl_name', f"Plan {attrs.get('pl_number', 'Unknown')}"),
                content=f"""Plan Number: {attrs.get('pl_number', 'N/A')}
Municipality: {attrs.get('plan_area_name', 'N/A')}
District: {attrs.get('district_name', 'N/A')}
Type: {attrs.get('entity_subtype_desc', 'N/A')}
Status: {attrs.get('station_desc', 'N/A')}
Area: {attrs.get('pl_area_dunam', 0)} dunam

Description: Planning regulation for {attrs.get('plan_area_name', 'area')}.
This is a {attrs.get('entity_subtype_desc', 'local plan')} currently at stage: {attrs.get('station_desc', 'unknown')}.
""",
                type=RegulationType.LOCAL_PLAN,
                jurisdiction=attrs.get('plan_area_name', 'Unknown'),
                effective_date=datetime.now(),
                metadata={
                    'plan_number': attrs.get('pl_number'),
                    'objectid': attrs.get('objectid'),
                    'district': attrs.get('district_name'),
                    'entity_subtype': attrs.get('entity_subtype_desc'),
                    'source': 'iPlan Sample Data'
                }
            )
            regulations.append(reg)
        except Exception as e:
            print(f"⚠️  Warning: Failed to convert plan {attrs.get('pl_number')}: {e}")
            continue

    print(f"✅ Created {len(regulations)} regulations")
    print()

    # Save to vector DB
    print("💾 Saving to vector database...")
    try:
        repo.save_batch(regulations)
        print(f"✅ Saved {len(regulations)} regulations")
        print()

        # Get stats
        stats = repo.get_statistics()
        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print()
        print(f"📊 Vector Database Stats:")
        print(f"  Total regulations: {stats.get('total_regulations', 0)}")
        print(f"  Collection: {stats.get('collection_name', 'N/A')}")
        print()

        print("🎉 You can now:")
        print("  • Open the web app and ask questions about these plans")
        print("  • Go to System Stats to see the indexed data")
        print("  • Search for plans by location or number")
        print()
        print("Example questions to try:")
        print('  - "What plans are there in Jerusalem?"')
        print('  - "Tell me about plan 101-0121850"')
        print('  - "What are the building regulations in Tel Aviv?"')
        print()

        return 0

    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

