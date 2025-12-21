"""
Usage Examples - GIS Architecture Agent with Clean Architecture

This module demonstrates how to use the new Clean Architecture implementation.
"""

from src.infrastructure.factory import get_factory
from src.application.dtos import (
    PlanSearchQuery,
    RegulationQuery,
    BuildingRightsQuery
)


def example_1_search_plans():
    """Example 1: Search for plans by location with vision analysis."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Search Plans with Vision Analysis")
    print("="*60 + "\n")
    
    # Get factory
    factory = get_factory()
    service = factory.get_plan_search_service()
    
    # Create search query
    query = PlanSearchQuery(
        location="תל אביב",
        include_vision_analysis=True,
        max_results=5
    )
    
    print(f"Searching for plans in: {query.location}")
    
    # Execute search
    result = service.search_plans(query)
    
    print(f"\nFound {result.total_found} plans in {result.execution_time_ms}ms\n")
    
    # Display results
    for idx, analyzed_plan in enumerate(result.plans, 1):
        plan = analyzed_plan.plan
        print(f"{idx}. {plan.name}")
        print(f"   Status: {plan.get_display_status()}")
        print(f"   Zone: {plan.zone_type.value if plan.zone_type else 'N/A'}")
        
        if analyzed_plan.vision_analysis:
            print(f"   Vision: {analyzed_plan.vision_analysis.description[:100]}...")
        
        print()


def example_2_query_regulations():
    """Example 2: Natural language query about regulations."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Query Regulations with Natural Language")
    print("="*60 + "\n")
    
    # Get factory
    factory = get_factory()
    service = factory.get_regulation_query_service()
    
    # Create query
    questions = [
        "What are the main provisions of TAMA 35?",
        "What parking requirements apply to residential buildings?",
        "What are the height restrictions in Tel Aviv?"
    ]
    
    for question in questions:
        print(f"Q: {question}")
        
        query = RegulationQuery(
            question=question,
            max_results=3
        )
        
        result = service.query(query)
        
        print(f"A: {result.answer[:200]}...")
        print(f"   ({len(result.regulations)} source regulations)\n")


def example_3_calculate_building_rights():
    """Example 3: Calculate building rights for a plot."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Calculate Building Rights")
    print("="*60 + "\n")
    
    # Get factory
    factory = get_factory()
    service = factory.get_building_rights_service()
    
    # Test different scenarios
    scenarios = [
        {"plot_size": 500.0, "zone_type": "residential_r2", "location": "תל אביב"},
        {"plot_size": 1000.0, "zone_type": "commercial", "location": "ירושלים"},
        {"plot_size": 300.0, "zone_type": "residential_r3", "location": "חיפה"},
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['plot_size']}sqm plot in {scenario['location']}")
        print(f"Zone Type: {scenario['zone_type']}")
        
        query = BuildingRightsQuery(
            plot_size=scenario['plot_size'],
            zone_type=scenario['zone_type'],
            location=scenario['location']
        )
        
        result = service.calculate_building_rights(query)
        rights = result.building_rights
        
        print(f"  Building Area: {rights.get_available_building_area():.0f} sqm")
        print(f"  Coverage: {rights.coverage_percent}%")
        print(f"  FAR: {rights.floor_area_ratio}")
        print(f"  Max Height: {rights.max_height_meters}m")
        print(f"  Parking: {rights.parking_requirement} spots")
        print()


def example_4_search_by_plan_id():
    """Example 4: Get specific plan by ID."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Get Plan by ID")
    print("="*60 + "\n")
    
    factory = get_factory()
    service = factory.get_plan_search_service()
    
    # Search for specific plan
    query = PlanSearchQuery(
        plan_id="101-0524683",
        include_vision_analysis=False
    )
    
    print(f"Fetching plan: {query.plan_id}")
    
    result = service.search_plans(query)
    
    if result.plans:
        plan = result.plans[0].plan
        print(f"\nFound: {plan.name}")
        print(f"Status: {plan.get_display_status()}")
        print(f"Location: {plan.location}")
        
        if plan.geometry:
            print(f"Area: {plan.geometry.calculate_area():.0f} sqm")
    else:
        print("Plan not found")


def example_5_regulation_by_type():
    """Example 5: Get regulations by type."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Get Regulations by Type")
    print("="*60 + "\n")
    
    factory = get_factory()
    repo = factory.get_regulation_repository()
    
    # Get TAMA regulations
    tama_regs = repo.get_by_type("tama", limit=5)
    
    print(f"Found {len(tama_regs)} TAMA regulations:\n")
    
    for reg in tama_regs:
        print(f"- {reg.title}")
        print(f"  Type: {reg.type.value}")
        print(f"  Jurisdiction: {reg.jurisdiction}")
        if reg.summary:
            print(f"  Summary: {reg.summary[:100]}...")
        print()


def example_6_cache_usage():
    """Example 6: Demonstrate caching."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Cache Service Usage")
    print("="*60 + "\n")
    
    factory = get_factory()
    cache = factory.get_cache_service()
    
    # Get cache stats
    stats = cache.get_stats()
    
    print("Cache Statistics:")
    print(f"  Total Entries: {stats['total_entries']}")
    print(f"  Valid Entries: {stats['valid_entries']}")
    print(f"  Expired Entries: {stats['expired_entries']}")
    print(f"  Total Size: {stats['total_size_mb']} MB")
    print(f"  Directory: {stats['cache_dir']}")
    
    # Test cache operations
    print("\nTesting cache operations...")
    
    cache.set("test_key", {"data": "test_value"}, ttl=3600)
    print("  ✓ Set test value")
    
    value = cache.get("test_key")
    print(f"  ✓ Retrieved: {value}")
    
    exists = cache.exists("test_key")
    print(f"  ✓ Exists check: {exists}")
    
    cache.delete("test_key")
    print("  ✓ Deleted test value")


def example_7_complete_workflow():
    """Example 7: Complete architecture firm workflow."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Complete Architecture Firm Workflow")
    print("="*60 + "\n")
    
    factory = get_factory()
    
    # Step 1: Search for plans
    print("Step 1: Search for relevant plans...")
    plan_service = factory.get_plan_search_service()
    plan_query = PlanSearchQuery(location="תל אביב", max_results=3)
    plan_result = plan_service.search_plans(plan_query)
    print(f"  Found {plan_result.total_found} plans\n")
    
    # Step 2: Check applicable regulations
    print("Step 2: Query applicable regulations...")
    reg_service = factory.get_regulation_query_service()
    reg_query = RegulationQuery(
        question="What are the building requirements in Tel Aviv?",
        max_results=3
    )
    reg_result = reg_service.query(reg_query)
    print(f"  Answer: {reg_result.answer[:150]}...\n")
    
    # Step 3: Calculate building rights
    print("Step 3: Calculate building rights...")
    rights_service = factory.get_building_rights_service()
    rights_query = BuildingRightsQuery(
        plot_size=600.0,
        zone_type="residential_r2",
        location="תל אביב"
    )
    rights_result = rights_service.calculate_building_rights(rights_query)
    rights = rights_result.building_rights
    print(f"  Max Building Area: {rights.get_available_building_area():.0f} sqm")
    print(f"  Max Height: {rights.max_height_meters}m")
    print(f"  Parking Required: {rights.parking_requirement} spots\n")
    
    # Step 4: Check compliance
    print("Step 4: Check compliance...")
    is_compliant = rights.is_compliant_height(20.0)
    print(f"  20m height compliant: {'Yes' if is_compliant else 'No'}")


def run_all_examples():
    """Run all examples."""
    print("\n" + "="*80)
    print("GIS ARCHITECTURE AGENT - USAGE EXAMPLES")
    print("Clean Architecture Implementation")
    print("="*80)
    
    try:
        example_1_search_plans()
        example_2_query_regulations()
        example_3_calculate_building_rights()
        example_4_search_by_plan_id()
        example_5_regulation_by_type()
        example_6_cache_usage()
        example_7_complete_workflow()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run specific example or all
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        example_func = f"example_{example_num}"
        
        if example_func in globals():
            globals()[example_func]()
        else:
            print(f"Example {example_num} not found")
            print("Available examples: 1-7, or run without arguments for all")
    else:
        run_all_examples()
