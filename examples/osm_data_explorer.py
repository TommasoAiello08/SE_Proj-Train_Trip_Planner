"""
OpenStreetMap Data Explorer per Provincie Italiane
Interroga Overpass API per ottenere:
1. Lista completa provincie italiane
2. Punti d'interesse (POI) per provincia
3. Verifica matching con stazioni Trenitalia
"""

import requests
import json
import time
from typing import List, Dict, Optional
from pathlib import Path

class OSMExplorer:
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.rate_limit = 1.0  # Secondi tra richieste (Nominatim: max 1/sec)
        
    def get_italian_provinces(self) -> List[Dict]:
        """
        Ottiene lista completa delle provincie italiane da OSM
        """
        print("🔍 Interrogo OSM per provincie italiane...")
        
        # Query Overpass per tutte le provincie (admin_level=6 in Italia)
        query = """
        [out:json][timeout:60];
        area["ISO3166-1"="IT"][admin_level=2];
        (
          relation(area)["admin_level"="6"]["boundary"="administrative"];
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            
            provinces = []
            for element in data.get("elements", []):
                if element.get("type") == "relation":
                    tags = element.get("tags", {})
                    if "name" in tags:
                        province = {
                            "osm_id": element.get("id"),
                            "name": tags.get("name"),
                            "name_it": tags.get("name:it", tags.get("name")),
                            "admin_level": tags.get("admin_level"),
                            "region": tags.get("is_in:region", tags.get("is_in")),
                            "wikidata": tags.get("wikidata"),
                            "wikipedia": tags.get("wikipedia:it")
                        }
                        provinces.append(province)
            
            print(f"✅ Trovate {len(provinces)} provincie")
            return provinces
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            return []
    
    def get_province_center(self, province_name: str) -> Optional[Dict]:
        """
        Ottiene coordinate del centro della provincia
        """
        time.sleep(self.rate_limit)  # Rate limiting
        
        params = {
            "q": f"{province_name}, Italia",
            "format": "json",
            "limit": 1
        }
        
        try:
            response = requests.get(
                self.nominatim_url,
                params=params,
                headers={"User-Agent": "TrainTripPlanner/1.0"}
            )
            response.raise_for_status()
            results = response.json()
            
            if results:
                return {
                    "lat": float(results[0]["lat"]),
                    "lon": float(results[0]["lon"]),
                    "display_name": results[0]["display_name"]
                }
        except Exception as e:
            print(f"⚠️  Errore coordinate {province_name}: {e}")
        
        return None
    
    def get_poi_categories(self, lat: float, lon: float, radius: int = 10000) -> Dict:
        """
        Ottiene POI per categoria in un raggio dal centro della provincia
        
        Args:
            lat: Latitudine centro
            lon: Longitudine centro  
            radius: Raggio in metri (default 10km)
        """
        
        # Categorie principali da cercare
        categories = {
            "tourism": ["museum", "attraction", "artwork", "gallery", "viewpoint", "monument"],
            "historic": ["monument", "castle", "ruins", "archaeological_site", "memorial"],
            "leisure": ["park", "garden", "nature_reserve"],
            "amenity": ["theatre", "cinema", "restaurant", "cafe"],
            "shop": ["mall"]
        }
        
        results = {}
        
        for main_cat, subcats in categories.items():
            print(f"  🔍 Cerco {main_cat}...")
            
            # Query Overpass per questa categoria
            subcat_query = "".join([f'node["{main_cat}"="{sc}"](around:{radius},{lat},{lon});' for sc in subcats])
            
            query = f"""
            [out:json][timeout:30];
            (
              {subcat_query}
              way["{main_cat}"](around:{radius},{lat},{lon});
            );
            out body;
            """
            
            try:
                response = requests.post(
                    self.overpass_url,
                    data={"data": query},
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                
                pois = []
                for element in data.get("elements", []):
                    tags = element.get("tags", {})
                    
                    # Estrai coordinate (node o centro way)
                    poi_lat = element.get("lat")
                    poi_lon = element.get("lon")
                    
                    if not poi_lat and element.get("type") == "way":
                        # Per way, usa primo nodo come approssimazione
                        continue
                    
                    poi = {
                        "osm_id": element.get("id"),
                        "name": tags.get("name", "Unnamed"),
                        "type": tags.get(main_cat),
                        "lat": poi_lat,
                        "lon": poi_lon,
                        "website": tags.get("website"),
                        "wikipedia": tags.get("wikipedia"),
                        "wikidata": tags.get("wikidata"),
                        "opening_hours": tags.get("opening_hours"),
                        "fee": tags.get("fee")
                    }
                    pois.append(poi)
                
                results[main_cat] = pois
                print(f"    ✅ {len(pois)} POI trovati")
                
                time.sleep(1)  # Rate limiting tra categorie
                
            except Exception as e:
                print(f"    ❌ Errore {main_cat}: {e}")
                results[main_cat] = []
        
        return results
    
    def search_train_station(self, city_name: str) -> Optional[Dict]:
        """
        Cerca stazione ferroviaria nella città (per matching con API Trenitalia)
        """
        time.sleep(self.rate_limit)
        
        params = {
            "q": f"stazione {city_name}",
            "format": "json",
            "limit": 5,
            "countrycodes": "it"
        }
        
        try:
            response = requests.get(
                self.nominatim_url,
                params=params,
                headers={"User-Agent": "TrainTripPlanner/1.0"}
            )
            response.raise_for_status()
            results = response.json()
            
            # Filtra risultati che contengono "stazione" o "railway"
            for result in results:
                display = result["display_name"].lower()
                if "stazione" in display or "railway" in display:
                    return {
                        "name": result["display_name"],
                        "lat": float(result["lat"]),
                        "lon": float(result["lon"]),
                        "osm_type": result["type"]
                    }
        except Exception as e:
            print(f"⚠️  Errore stazione {city_name}: {e}")
        
        return None


def demo_full_exploration():
    """
    Demo completo: estrae provincie + POI + matching stazioni
    """
    explorer = OSMExplorer()
    
    print("="*60)
    print("🇮🇹 OSM DATA PULL - PROVINCIE ITALIANE")
    print("="*60)
    
    # Step 1: Ottieni tutte le provincie
    provinces = explorer.get_italian_provinces()
    
    if not provinces:
        print("❌ Nessuna provincia trovata!")
        return
    
    print(f"\n📊 PROVINCIE TROVATE: {len(provinces)}")
    print("-"*60)
    
    # Mostra prime 10
    for i, prov in enumerate(provinces[:10], 1):
        print(f"{i:2d}. {prov['name']:30s} (Regione: {prov.get('region', 'N/A')})")
    
    if len(provinces) > 10:
        print(f"    ... e altre {len(provinces) - 10} provincie")
    
    # Step 2: Demo dettagliato su 3 provincie campione
    print("\n" + "="*60)
    print("🔬 ANALISI DETTAGLIATA - 3 Provincie Campione")
    print("="*60)
    
    sample_provinces = ["Milano", "Firenze", "Roma"]
    detailed_data = {}
    
    for prov_name in sample_provinces:
        print(f"\n🏛️  {prov_name.upper()}")
        print("-"*60)
        
        # Trova coordinate centro
        center = explorer.get_province_center(prov_name)
        if not center:
            print(f"⚠️  Coordinate non trovate per {prov_name}")
            continue
        
        print(f"📍 Centro: {center['lat']:.4f}, {center['lon']:.4f}")
        
        # Cerca stazione ferroviaria
        station = explorer.search_train_station(prov_name)
        if station:
            print(f"🚂 Stazione: {station['name']}")
        else:
            print(f"⚠️  Stazione non trovata")
        
        # Ottieni POI (raggio 10km dal centro)
        print(f"\n🎯 POI nel raggio di 10km:")
        pois = explorer.get_poi_categories(center['lat'], center['lon'], radius=10000)
        
        total_pois = sum(len(v) for v in pois.values())
        print(f"\n📊 TOTALE POI: {total_pois}")
        
        for category, items in pois.items():
            if items:
                print(f"  • {category:15s}: {len(items):3d} POI")
                # Mostra primi 3
                for poi in items[:3]:
                    print(f"    - {poi['name'][:50]}")
        
        detailed_data[prov_name] = {
            "center": center,
            "station": station,
            "pois": pois,
            "total_pois": total_pois
        }
        
        time.sleep(2)  # Pausa tra provincie
    
    # Step 3: Salva risultati
    output_file = Path(__file__).parent.parent / "data" / "osm_provinces_sample.json"
    
    save_data = {
        "metadata": {
            "date": "2026-01-02",
            "total_provinces": len(provinces),
            "sample_analyzed": len(sample_provinces)
        },
        "all_provinces": provinces,
        "detailed_analysis": detailed_data
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"💾 Dati salvati in: {output_file}")
    print("="*60)
    
    # Step 4: Statistiche finali
    print("\n📈 STATISTICHE FINALI:")
    print("-"*60)
    print(f"Provincie totali in Italia: {len(provinces)}")
    print(f"Provincie analizzate in dettaglio: {len(detailed_data)}")
    
    for prov, data in detailed_data.items():
        print(f"\n{prov}:")
        print(f"  • POI totali: {data['total_pois']}")
        print(f"  • Stazione: {'✅ Trovata' if data['station'] else '❌ Non trovata'}")
        print(f"  • Coordinate: ✅")
    
    print("\n✅ Esplorazione completata!")
    
    return save_data


def quick_province_list():
    """
    Lista veloce solo nomi provincie (senza POI)
    """
    explorer = OSMExplorer()
    
    print("🔍 Ottengo lista veloce provincie italiane...")
    provinces = explorer.get_italian_provinces()
    
    print(f"\n📋 {len(provinces)} PROVINCIE ITALIANE:\n")
    
    # Raggruppa per regione
    by_region = {}
    for prov in provinces:
        region = prov.get('region', 'Sconosciuta')
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(prov['name'])
    
    for region, provs in sorted(by_region.items()):
        print(f"\n{region}:")
        for prov in sorted(provs):
            print(f"  • {prov}")
    
    return provinces


if __name__ == "__main__":
    print("Scegli modalità:")
    print("1. Lista veloce provincie (solo nomi)")
    print("2. Analisi completa (provincie + POI + stazioni)")
    
    choice = input("\nScelta [1/2]: ").strip()
    
    if choice == "1":
        quick_province_list()
    else:
        demo_full_exploration()
