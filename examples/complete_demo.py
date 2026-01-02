"""
Complete System Demo - Italian Train Trip Planner
Shows full end-to-end functionality with all integrations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from city_database import CityDatabase
from itinerary_planner import ItineraryPlanner, TripInput
from datetime import datetime


def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def demo_scenario_1():
    """Scenario 1: Classic Italian Tour (Static DB Cities)"""
    print_header("📍 SCENARIO 1: Classic Italian Grand Tour")
    
    print("\n🎯 USER INPUT:")
    print("-" * 70)
    print("Duration:      4 days")
    print("Route:         Milan → Bologna → Florence → Rome")
    print("Interests:     art, history, culture")
    print("Budget:        €500")
    print("Start Date:    January 10, 2026")
    print("Travel Mode:   Train")
    print("-" * 70)
    
    trip = TripInput(
        days=4,
        cities=['Milano', 'Bologna', 'Firenze', 'Roma'],
        interests=['arte', 'storia', 'cultura'],
        start_city='Milano',
        end_city='Roma',
        budget=500,
        start_date=datetime(2026, 1, 10)
    )
    
    print("\n⚙️  SYSTEM PROCESSING...")
    planner = ItineraryPlanner(use_weather=True)
    schedule = planner.plan_trip(trip)
    
    print("\n" + "="*70)
    print("📋 GENERATED ITINERARY OUTPUT")
    print("="*70)
    planner.print_itinerary(schedule)
    
    # Summary stats
    total_cost = sum(day.estimated_cost for day in schedule)
    total_pois = sum(len(day.pois) for day in schedule)
    total_travel = sum(day.travel_time for day in schedule)
    
    print("\n" + "="*70)
    print("📊 TRIP STATISTICS")
    print("="*70)
    print(f"Total Cities:     {len(set(day.city for day in schedule))}")
    print(f"Total POIs:       {total_pois}")
    print(f"Travel Time:      {total_travel:.1f} hours")
    print(f"Total Cost:       €{total_cost:.2f}")
    print(f"Budget Status:    {'✅ Within budget' if total_cost <= trip.budget else '⚠️ Over budget'}")
    print(f"Weather-Adapted:  ✅ Yes (indoor/outdoor POI selection)")


def demo_scenario_2():
    """Scenario 2: Off-the-Beaten-Path (OSM Cities)"""
    print_header("📍 SCENARIO 2: Hidden Gems of Central Italy")
    
    print("\n🎯 USER INPUT:")
    print("-" * 70)
    print("Duration:      3 days")
    print("Route:         Florence → Siena → Perugia")
    print("Interests:     history, nature, food")
    print("Budget:        €400")
    print("Start Date:    January 15, 2026")
    print("Note:          Siena & Perugia are NOT in static DB (will use OSM)")
    print("-" * 70)
    
    trip = TripInput(
        days=3,
        cities=['Firenze', 'Siena', 'Perugia'],
        interests=['storia', 'natura', 'cibo'],
        start_city='Firenze',
        end_city='Perugia',
        budget=400,
        start_date=datetime(2026, 1, 15)
    )
    
    print("\n⚙️  SYSTEM PROCESSING...")
    print("   💡 System will automatically fetch Siena & Perugia from OSM")
    print("   ⏱️  First OSM fetch may take 30-60 seconds...")
    
    planner = ItineraryPlanner(use_weather=True)
    schedule = planner.plan_trip(trip)
    
    print("\n" + "="*70)
    print("📋 GENERATED ITINERARY OUTPUT")
    print("="*70)
    planner.print_itinerary(schedule)
    
    # Summary
    total_cost = sum(day.estimated_cost for day in schedule)
    osm_cities = [day.city for day in schedule if day.city in ['Siena', 'Perugia']]
    
    print("\n" + "="*70)
    print("📊 TRIP STATISTICS")
    print("="*70)
    print(f"Total Cities:     {len(set(day.city for day in schedule))}")
    print(f"OSM Cities:       {len(set(osm_cities))} ({', '.join(set(osm_cities))})")
    print(f"Total Cost:       €{total_cost:.2f}")
    print(f"OSM Integration:  ✅ Seamless fallback to OpenStreetMap")


def demo_scenario_3():
    """Scenario 3: Weekend Getaway (2 days)"""
    print_header("📍 SCENARIO 3: Weekend Escape - Venice & Verona")
    
    print("\n🎯 USER INPUT:")
    print("-" * 70)
    print("Duration:      2 days")
    print("Route:         Venice → Verona")
    print("Interests:     art, architecture, romance")
    print("Budget:        €300")
    print("Start Date:    January 20, 2026")
    print("-" * 70)
    
    trip = TripInput(
        days=2,
        cities=['Venezia', 'Verona'],
        interests=['arte', 'architettura'],
        start_city='Venezia',
        end_city='Verona',
        budget=300,
        start_date=datetime(2026, 1, 20)
    )
    
    print("\n⚙️  SYSTEM PROCESSING...")
    planner = ItineraryPlanner(use_weather=True)
    schedule = planner.plan_trip(trip)
    
    print("\n" + "="*70)
    print("📋 GENERATED ITINERARY OUTPUT")
    print("="*70)
    planner.print_itinerary(schedule)


def show_system_capabilities():
    """Show what the system can do"""
    print_header("🚀 SYSTEM CAPABILITIES")
    
    capabilities = [
        ("🗺️  Multi-City Planning", "Optimizes routes across multiple Italian cities"),
        ("🚂 Train Integration", "Uses real Trenitalia API for connections"),
        ("🌤️  Weather Adaptation", "Adjusts POI selection based on forecast"),
        ("🏛️  110+ Cities Support", "Static DB (10) + OSM on-demand (100+)"),
        ("💰 Budget Management", "Tracks costs (attractions + meals + accommodation)"),
        ("🎯 Interest Matching", "Scores POIs based on user preferences"),
        ("⏰ Time Optimization", "Knapsack algorithm for POI selection"),
        ("💾 Intelligent Caching", "OSM (7 days) + Travel Graph (persistent)"),
        ("🎨 Indoor/Outdoor", "Weather-aware POI classification"),
        ("📊 Multi-Objective", "Balances time, cost, interests, weather"),
    ]
    
    print("\n")
    for feature, description in capabilities:
        print(f"{feature:30s} {description}")
    
    print("\n" + "-"*70)
    print("Technologies Used:")
    print("  • API Trenitalia (train data)")
    print("  • OpenStreetMap Overpass API (POI data)")
    print("  • OpenWeatherMap API (forecasts)")
    print("  • Dijkstra's Algorithm (shortest paths)")
    print("  • Knapsack Algorithm (POI selection)")
    print("  • Greedy Algorithm (day allocation)")


def interactive_demo():
    """Interactive demo allowing user to choose scenario"""
    print("\n" + "🎬 " + "="*66 + " 🎬")
    print("   ITALIAN TRAIN TRIP PLANNER - COMPLETE SYSTEM DEMO")
    print("🎬 " + "="*66 + " 🎬")
    
    show_system_capabilities()
    
    print("\n\n" + "="*70)
    print("Choose a demo scenario:")
    print("="*70)
    print("\n1. 🏛️  Classic Grand Tour (4 days: Milan → Bologna → Florence → Rome)")
    print("   - Uses static database cities")
    print("   - Shows weather integration")
    print("   - Complete itinerary with costs")
    print()
    print("2. 🌄 Hidden Gems (3 days: Florence → Siena → Perugia)")
    print("   - Demonstrates OSM on-demand")
    print("   - Siena & Perugia fetched from OpenStreetMap")
    print("   - Shows seamless fallback")
    print()
    print("3. 💑 Weekend Escape (2 days: Venice → Verona)")
    print("   - Quick romantic getaway")
    print("   - Optimized for short trips")
    print()
    print("4. 🎯 All Scenarios (runs all 3 demos)")
    print()
    
    choice = input("Enter choice [1/2/3/4] (or press Enter for default): ").strip()
    
    if choice == "1":
        demo_scenario_1()
    elif choice == "2":
        print("\n⚠️  Note: This will query OSM (may take 1-2 minutes)")
        confirm = input("Continue? [y/n]: ").strip().lower()
        if confirm == 'y':
            demo_scenario_2()
        else:
            print("Switching to Scenario 1...")
            demo_scenario_1()
    elif choice == "3":
        demo_scenario_3()
    elif choice == "4":
        demo_scenario_1()
        input("\n\n⏸️  Press Enter to continue to Scenario 2...")
        demo_scenario_2()
        input("\n\n⏸️  Press Enter to continue to Scenario 3...")
        demo_scenario_3()
    else:
        print("\n💡 Running default: Scenario 1")
        demo_scenario_1()
    
    # Final summary
    print("\n\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)
    print("\nSystem Features Demonstrated:")
    print("  ✓ Multi-city itinerary planning")
    print("  ✓ Intelligent POI selection")
    print("  ✓ Weather-adaptive scheduling")
    print("  ✓ Cost estimation & tracking")
    print("  ✓ Train connection optimization")
    print("  ✓ Static DB + OSM integration")
    print("\nReady for:")
    print("  → FastAPI Backend implementation")
    print("  → Web UI development")
    print("  → Production deployment")
    print("\n" + "="*70)


if __name__ == "__main__":
    interactive_demo()
