"""
API Trenitalia Explorer - Analisi completa dei dati disponibili
Questo script esplora tutte le funzionalità dell'API per capire quali dati possiamo utilizzare
per il Constraint-Based Train Trip Planner
"""

from datetime import datetime
from apitr import apitr
import json

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def analyze_api():
    api = apitr(decodeJson=True)
    
    # Test con Milano Centrale e Roma Termini
    stazione_partenza = "MILANO CENTRALE"
    stazione_arrivo = "ROMA TERMINI"
    
    print_section("1. RICERCA STAZIONI")
    print(f"Ricerca stazione: {stazione_partenza}")
    stazioni_milano = api.searchStazione(stazione_partenza)
    print(f"Risultati trovati: {len(stazioni_milano) if stazioni_milano else 0}")
    if stazioni_milano and len(stazioni_milano) > 0:
        print("\nPrima stazione trovata:")
        print(json.dumps(stazioni_milano[0], indent=2, ensure_ascii=False))
        
        print("\n📊 CAMPI DISPONIBILI PER STAZIONE:")
        if stazioni_milano[0]:
            for key in stazioni_milano[0].keys():
                print(f"  - {key}: {type(stazioni_milano[0][key]).__name__}")
    
    # Ottieni codici stazione
    cod_milano = api.getCodStazione(stazione_partenza)
    cod_roma = api.getCodStazione(stazione_arrivo)
    
    print(f"\n✅ Codice stazione Milano Centrale: {cod_milano}")
    print(f"✅ Codice stazione Roma Termini: {cod_roma}")
    
    
    print_section("2. INFORMAZIONI MOBILITÀ (Avvisi di servizio)")
    info_mob = api.getInfoMob()
    if isinstance(info_mob, str):
        print(f"Dati ricevuti come stringa (probabile HTML/XML)")
        print(f"Lunghezza: {len(info_mob)} caratteri")
        print("\nPrimi 500 caratteri:")
        print(info_mob[:500])
    elif info_mob and len(info_mob) > 0:
        print(f"Numero avvisi: {len(info_mob)}")
        print("\nPrimo avviso:")
        print(json.dumps(info_mob[0], indent=2, ensure_ascii=False))
        
        print("\n📊 CAMPI DISPONIBILI PER AVVISI:")
        if isinstance(info_mob[0], dict):
            for key in info_mob[0].keys():
                print(f"  - {key}: {type(info_mob[0][key]).__name__}")
    
    
    print_section("3. PARTENZE DA MILANO CENTRALE")
    ora_corrente = datetime.now()
    partenze = api.getPartenze(cod_milano, ora_corrente)
    print(f"Numero treni in partenza: {len(partenze) if partenze else 0}")
    
    if partenze and len(partenze) > 0:
        print("\nPrimo treno in partenza:")
        print(json.dumps(partenze[0], indent=2, ensure_ascii=False))
        
        print("\n📊 CAMPI DISPONIBILI PER PARTENZE:")
        for key in partenze[0].keys():
            print(f"  - {key}: {type(partenze[0][key]).__name__}")
        
        # Analisi statistica
        print("\n📈 ANALISI DATI PARTENZE:")
        treni_ritardo = sum(1 for t in partenze if t.get('ritardo', 0) > 0)
        print(f"  - Treni in ritardo: {treni_ritardo}/{len(partenze)}")
        print(f"  - Treni puntuali: {len(partenze) - treni_ritardo}/{len(partenze)}")
        
        destinazioni = set(t.get('destinazione', 'N/A') for t in partenze)
        print(f"  - Destinazioni uniche: {len(destinazioni)}")
    
    
    print_section("4. ARRIVI A ROMA TERMINI")
    arrivi = api.getArrivi(cod_roma, ora_corrente)
    print(f"Numero treni in arrivo: {len(arrivi) if arrivi else 0}")
    
    if arrivi and len(arrivi) > 0:
        print("\nPrimo treno in arrivo:")
        print(json.dumps(arrivi[0], indent=2, ensure_ascii=False))
        
        print("\n📊 CAMPI DISPONIBILI PER ARRIVI:")
        for key in arrivi[0].keys():
            print(f"  - {key}: {type(arrivi[0][key]).__name__}")
    
    
    print_section("5. SOLUZIONI DI VIAGGIO (Milano → Roma)")
    soluzioni = api.getIndicazioniViaggio(cod_milano, cod_roma, ora_corrente)
    print(f"Numero soluzioni trovate: {len(soluzioni) if soluzioni else 0}")
    
    if soluzioni and len(soluzioni) > 0:
        print("\nPrima soluzione di viaggio:")
        print(json.dumps(soluzioni[0], indent=2, ensure_ascii=False))
        
        print("\n📊 CAMPI DISPONIBILI PER SOLUZIONI VIAGGIO:")
        for key in soluzioni[0].keys():
            print(f"  - {key}: {type(soluzioni[0][key]).__name__}")
        
        # Analisi dettagliata
        print("\n📈 ANALISI SOLUZIONI DI VIAGGIO:")
        for i, sol in enumerate(soluzioni[:3]):  # Prime 3 soluzioni
            print(f"\n  Soluzione {i+1}:")
            print(f"    - Partenza: {sol.get('orarioPartenza', 'N/A')}")
            print(f"    - Arrivo: {sol.get('orarioArrivo', 'N/A')}")
            print(f"    - Durata: {sol.get('durata', 'N/A')}")
            print(f"    - Cambi: {sol.get('cambi', 'N/A')}")
            print(f"    - Soluzione: {sol.get('soluzione', 'N/A')}")
    
    
    print_section("6. ANDAMENTO TRENO (Dettagli treno in tempo reale)")
    # Prendiamo il primo treno dalle partenze per testare
    if partenze and len(partenze) > 0:
        primo_treno = partenze[0]
        numero_treno = str(primo_treno.get('numeroTreno'))  # Converti a stringa
        cod_origine = primo_treno.get('codOrigine', cod_milano)
        
        print(f"Analizziamo il treno: {numero_treno}")
        
        andamento = api.getAndamento(cod_origine, numero_treno, ora_corrente)
        
        if andamento:
            print("\nDati andamento treno:")
            print(json.dumps(andamento, indent=2, ensure_ascii=False)[:2000])  # Limitiamo output
            
            print("\n📊 CAMPI DISPONIBILI PER ANDAMENTO TRENO:")
            for key in andamento.keys():
                print(f"  - {key}: {type(andamento[key]).__name__}")
            
            # Informazioni chiave
            print("\n📈 INFORMAZIONI CHIAVE TRENO:")
            print(f"  - Origine: {andamento.get('origine', 'N/A')}")
            print(f"  - Destinazione: {andamento.get('destinazione', 'N/A')}")
            print(f"  - Categoria: {andamento.get('categoria', 'N/A')}")
            print(f"  - Ritardo: {andamento.get('ritardo', 'N/A')} minuti")
            print(f"  - Provvedimenti: {andamento.get('provvedimento', 'N/A')}")
            
            # Fermate
            if 'fermate' in andamento and andamento['fermate']:
                print(f"\n  - Numero fermate: {len(andamento['fermate'])}")
                print("  - Prime 3 fermate:")
                for fermata in andamento['fermate'][:3]:
                    print(f"    • {fermata.get('stazione', 'N/A')}")
                    print(f"      Arrivo: {fermata.get('arrivo_teorico', 'N/A')} (previsto: {fermata.get('arrivoReale', 'N/A')})")
                    print(f"      Partenza: {fermata.get('partenza_teorica', 'N/A')} (prevista: {fermata.get('partenzaReale', 'N/A')})")
    
    
    print_section("7. STAZIONI PER REGIONE")
    print("Test: Stazioni in Lombardia (codice: 1)")
    stazioni_lombardia = api.getStazioniByRegione("1")
    print(f"Numero stazioni in Lombardia: {len(stazioni_lombardia) if stazioni_lombardia else 0}")
    
    if stazioni_lombardia and len(stazioni_lombardia) > 0:
        print("\nPrime 3 stazioni:")
        for stazione in stazioni_lombardia[:3]:
            print(f"  - {stazione}")
    
    
    print_section("RIEPILOGO DATI DISPONIBILI PER IL PLANNER")
    print("""
✅ DATI DISPONIBILI dall'API Trenitalia:

1. STAZIONI:
   - Ricerca per nome
   - Codice identificativo
   - Nome lungo e breve
   - Coordinate geografiche (se disponibili)
   - Elenco stazioni per regione

2. PARTENZE/ARRIVI:
   - Numero treno
   - Destinazione/Origine
   - Orario programmato e effettivo
   - Ritardo in minuti
   - Binario
   - Categoria treno (FR, IC, REG, ecc.)

3. SOLUZIONI DI VIAGGIO:
   - Orari partenza/arrivo
   - Durata totale
   - Numero cambi
   - Dettagli tratta per tratta
   - Tutti i treni coinvolti

4. ANDAMENTO TRENO IN TEMPO REALE:
   - Posizione corrente
   - Tutte le fermate (passate e future)
   - Ritardi per ogni fermata
   - Orari teorici vs reali
   - Provvedimenti/cancellazioni
   - Binari effettivi

5. INFORMAZIONI MOBILITÀ:
   - Avvisi di servizio
   - Problemi sulla rete
   - Cancellazioni programmate

📊 POSSIBILI CONSTRAINT PER IL PLANNER:

Basandoci sui dati disponibili, possiamo implementare:
- ⏰ Orario preferito (partenza/arrivo)
- 🔄 Numero massimo cambi
- ⏱️ Durata massima viaggio
- 🚂 Categoria treno (solo FR, no Regionali, ecc.)
- 🕐 Ritardo massimo accettabile
- 🌤️ Condizioni meteo (con OpenWeather)
- 🗺️ Distanza dalla stazione (con OSM)
- 💰 Prezzo (se disponibile da altre fonti)

🔗 INTEGRAZIONE CON ALTRE API:

OpenStreetMap (OSM):
- Coordinate stazioni
- Distanza da punto specifico
- Servizi nelle vicinanze (hotel, ristoranti)
- Percorsi per raggiungere la stazione

OpenWeather:
- Condizioni meteo alla partenza/arrivo
- Previsioni per evitare maltempo
- Alert meteo per pianificare meglio
    """)


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║   API TRENITALIA EXPLORER - Analisi Completa                  ║
    ║   Constraint-Based Train Trip Planner - SE Project            ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        analyze_api()
        
        print_section("ESECUZIONE COMPLETATA")
        print("✅ Analisi API completata con successo!")
        print("\n💡 Prossimi passi suggeriti:")
        print("   1. Definire i constraint del planner")
        print("   2. Integrare OpenStreetMap per dati geografici")
        print("   3. Integrare OpenWeather per dati meteo")
        print("   4. Progettare l'algoritmo di pianificazione")
        print("   5. Implementare il sistema di constraint satisfaction")
        
    except Exception as e:
        print(f"\n❌ ERRORE durante l'esecuzione: {str(e)}")
        import traceback
        traceback.print_exc()
