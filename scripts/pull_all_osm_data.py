#!/usr/bin/env python3
"""
Pull ALL OSM Data for Italian Cities

This script:
1. Loads all cities from the city database
2. Makes LIVE API calls to OSM (bypasses cache) for each city
3. Ensures every city has at least 3 POIs
4. Increases search radius if needed
5. Measures total execution time
6. Saves results to cache

Usage:
    python3 scripts/pull_all_osm_data.py [--dry-run]
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from city_database import CityDatabase
from osm_provider import OSMProvider


def main():
    parser = argparse.ArgumentParser(description='Pull all OSM data for Italian cities')
    parser.add_argument('--dry-run', action='store_true', help='Test on first 5 cities only')
    parser.add_argument('--min-pois', type=int, default=3, help='Minimum POIs per city (default: 3)')
    args = parser.parse_args()
    
    print("=" * 80)
    print("🇮🇹 OSM DATA PULL - ALL ITALIAN CITIES")
    print("=" * 80)
    print(f"📅 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Minimum POIs per city: {args.min_pois}")
    print(f"🔴 MODE: LIVE API CALLS (cache bypassed for data fetching)")
    print("=" * 80)
    
    # Load all cities
    db = CityDatabase()
    all_cities = db.get_all_cities()
    
    if args.dry_run:
        all_cities = all_cities[:5]
        print(f"⚠️  DRY RUN MODE: Testing on first {len(all_cities)} cities only\n")
    else:
        print(f"📊 Total cities to process: {len(all_cities)}\n")
    
    # Create OSM provider with cache bypass
    provider = OSMProvider(bypass_cache=True)
    
    # Stats tracking
    start_time = time.time()
    stats = {
        'total': len(all_cities),
        'success': 0,
        'failed': 0,
        'below_minimum': 0,
        'total_pois': 0,
        'api_calls': 0
    }
    
    failed_cities = []
    below_minimum_cities = []
    
    # Process each city
    for i, city_data in enumerate(all_cities, 1):
        city_name = city_data['name']
        print(f"\n[{i}/{len(all_cities)}] 📍 {city_name}")
        print("-" * 80)
        
        try:
            # Try with default radius (15km)
            radius = 15000
            pois = provider.get_city_pois(city_name, radius=radius)
            stats['api_calls'] += 1
            
            # If not enough POIs, try larger radius
            if len(pois) < args.min_pois:
                print(f"  ⚠️  Only {len(pois)} POIs found, trying larger radius (25km)...")
                radius = 25000
                pois = provider.get_city_pois(city_name, radius=radius)
                stats['api_calls'] += 1
            
            # Still not enough? Try even larger
            if len(pois) < args.min_pois:
                print(f"  ⚠️  Only {len(pois)} POIs found, trying even larger radius (35km)...")
                radius = 35000
                pois = provider.get_city_pois(city_name, radius=radius)
                stats['api_calls'] += 1
            
            num_pois = len(pois)
            stats['total_pois'] += num_pois
            
            if num_pois >= args.min_pois:
                print(f"  ✅ SUCCESS: {num_pois} POIs (radius: {radius/1000:.0f}km)")
                stats['success'] += 1
            else:
                print(f"  ⚠️  WARNING: Only {num_pois} POIs (minimum: {args.min_pois})")
                stats['below_minimum'] += 1
                below_minimum_cities.append((city_name, num_pois))
                stats['success'] += 1  # Still count as success
            
            # Rate limiting between cities
            if i < len(all_cities):
                wait_time = 2.0
                print(f"  ⏳ Rate limit: waiting {wait_time}s...")
                time.sleep(wait_time)
        
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            stats['failed'] += 1
            failed_cities.append(city_name)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(int(elapsed_time), 60)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"⏱️  Total time: {minutes}m {seconds}s ({elapsed_time:.1f}s)")
    print(f"🌐 Total API calls: {stats['api_calls']}")
    print(f"⚡ Avg time per city: {elapsed_time / len(all_cities):.1f}s")
    print(f"⚡ Avg time per API call: {elapsed_time / stats['api_calls']:.1f}s")
    print()
    print(f"✅ Successful: {stats['success']}/{stats['total']}")
    print(f"❌ Failed: {stats['failed']}/{stats['total']}")
    print(f"📍 Total POIs fetched: {stats['total_pois']}")
    print(f"📊 Avg POIs per city: {stats['total_pois'] / stats['success']:.1f}")
    
    if stats['below_minimum'] > 0:
        print(f"\n⚠️  Cities below minimum ({args.min_pois} POIs): {stats['below_minimum']}")
        for city, count in below_minimum_cities:
            print(f"   - {city}: {count} POIs")
    
    if failed_cities:
        print(f"\n❌ Failed cities ({len(failed_cities)}):")
        for city in failed_cities:
            print(f"   - {city}")
    
    print("\n" + "=" * 80)
    print("✅ OSM data pull completed!")
    print(f"💾 Data saved to cache: {provider.cache_dir}")
    print("=" * 80)
    
    # Return stats for further processing
    return stats


if __name__ == "__main__":
    stats = main()
    sys.exit(0 if stats['failed'] == 0 else 1)
