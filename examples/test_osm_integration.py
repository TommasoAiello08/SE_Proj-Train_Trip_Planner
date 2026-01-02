"""
Test OSM On-Demand Integration
Tests the city database OSM fallback with cities not in static DB
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from city_database import CityDatabase
from itinerary_planner import ItineraryPlanner, TripInput
from datetime import datetime

def test_osm_city_fetch():
    """Test fetching a single city from OSM"""
    print("\n" + "="*70)
    print("🧪 TEST 1: Single City from OSM")
    print("="*70)
    
    db = CityDatabase(use_osm=True)
    
    # Test with a city NOT in static database
    test_city = "Perugia"
    
    print(f"\n🌐 Fetching '{test_city}' (not in static DB)...")
    print("⏱️  This will take 30-60 seconds for first fetch...\n")
    
    city_data = db.get_city_by_name(test_city)
    
    if city_data:
        print(f"\n✅ SUCCESS: {test_city} fetched from OSM!")
        print(f"📍 Location: {city_data['latitude']:.4f}, {city_data['longitude']:.4f}")
        print(f"🏛️  Region: {city_data['region']}")
        print(f"🚂 Station: {city_data['station_code']}")
        print(f"🎯 POIs found: {len(city_data['attractions'])}")
        print(f"📂 Categories: {', '.join(city_data['categories'])}")
        
        if city_data['attractions']:
            print(f"\n🎨 Top 5 Attractions:")
            for poi in city_data['attractions'][:5]:
                print(f"  • {poi['name']} (⭐{poi['rating']}, {poi['duration_hours']}h, €{poi['cost']})")
        
        return city_data
    else:
        print(f"\n❌ FAILED: Could not fetch {test_city}")
        return None


def test_osm_itinerary():
    """Test full itinerary with OSM city"""
    print("\n\n" + "="*70)
    print("🧪 TEST 2: Itinerary with OSM City")
    print("="*70)
    print("\n📋 Route: Milan → Perugia → Florence → Rome (4 days)")
    print("   • Milan, Florence, Rome: static DB")
    print("   • Perugia: OSM on-demand\n")
    
    trip = TripInput(
        days=4,
        cities=['Milano', 'Perugia', 'Firenze', 'Roma'],
        interests=['arte', 'storia', 'cultura'],
        start_city='Milano',
        end_city='Roma',
        budget=600,
        start_date=datetime(2026, 1, 15)
    )
    
    print("⚠️  Note: Perugia fetch will take ~60 seconds on first run")
    print("💾 Subsequent runs will use cache (instant)\n")
    
    planner = ItineraryPlanner()
    
    try:
        schedule = planner.plan_trip(trip)
        planner.print_itinerary(schedule)
        
        print("\n✅ SUCCESS: Itinerary created with OSM city!")
        return schedule
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_osm_cache():
    """Test that OSM cache works on second fetch"""
    print("\n\n" + "="*70)
    print("🧪 TEST 3: OSM Cache Performance")
    print("="*70)
    
    db = CityDatabase(use_osm=True)
    test_city = "Padova"
    
    import time
    
    # First fetch (should take ~60s)
    print(f"\n⏱️  First fetch of '{test_city}' (will be slow)...")
    start = time.time()
    city1 = db.get_city_by_name(test_city)
    duration1 = time.time() - start
    
    if city1:
        print(f"✅ First fetch: {duration1:.1f} seconds")
        print(f"   Found {len(city1['attractions'])} POIs")
    
    # Second fetch (should be instant from cache)
    print(f"\n⚡ Second fetch of '{test_city}' (should be cached)...")
    start = time.time()
    city2 = db.get_city_by_name(test_city)
    duration2 = time.time() - start
    
    if city2:
        print(f"✅ Second fetch: {duration2:.1f} seconds")
        print(f"   Cache speedup: {duration1/max(duration2, 0.001):.0f}x faster!")
    
    # Verify same data
    if city1 and city2:
        if city1 == city2:
            print("\n✅ Cache integrity verified: data matches perfectly")
        else:
            print("\n⚠️  Cache data differs from original")


def check_cache_location():
    """Show where OSM cache is stored"""
    print("\n\n" + "="*70)
    print("📁 OSM Cache Location")
    print("="*70)
    
    cache_dir = Path(__file__).parent.parent / "cache" / "osm"
    
    print(f"\n📂 Cache directory: {cache_dir}")
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        print(f"📦 Cached cities: {len(cache_files)}")
        
        if cache_files:
            print("\n🗂️  Cached files:")
            for f in cache_files:
                size_kb = f.stat().st_size / 1024
                print(f"  • {f.name} ({size_kb:.1f} KB)")
    else:
        print("⚠️  Cache directory doesn't exist yet")
        print("   Will be created on first OSM query")


if __name__ == "__main__":
    print("\n🚀 OSM ON-DEMAND INTEGRATION TESTS")
    print("="*70)
    
    # Show cache status first
    check_cache_location()
    
    # Choose test
    print("\n\n🎯 Choose test:")
    print("1. Quick test: Single city from OSM (Perugia)")
    print("2. Full test: Complete itinerary with OSM city")
    print("3. Cache test: Verify caching performance (Padova)")
    print("4. All tests (will take 3-5 minutes)")
    
    choice = input("\nChoice [1/2/3/4]: ").strip()
    
    if choice == "1":
        test_osm_city_fetch()
    elif choice == "2":
        test_osm_itinerary()
    elif choice == "3":
        test_osm_cache()
    elif choice == "4":
        print("\n⏳ Running all tests (this will take a few minutes)...\n")
        test_osm_city_fetch()
        test_osm_itinerary()
        test_osm_cache()
    else:
        print("\n💡 Default: Running quick test")
        test_osm_city_fetch()
    
    # Show final cache status
    check_cache_location()
    
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)
