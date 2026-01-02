"""
Esempio Pratico - Constraint-Based Train Trip Planner
Dimostra l'uso di vari constraint per pianificare un viaggio in treno
"""

from datetime import datetime, timedelta
from apitr import apitr
import json

class TripConstraint:
    """Classe base per tutti i constraint"""
    def __init__(self, weight=1.0, is_hard=True):
        self.weight = weight
        self.is_hard = is_hard  # True = must satisfy, False = nice to have
    
    def evaluate(self, solution):
        """Restituisce True se il constraint è soddisfatto, False altrimenti"""
        raise NotImplementedError
    
    def score(self, solution):
        """Restituisce un punteggio 0-1 per soft constraints"""
        return 1.0 if self.evaluate(solution) else 0.0


class MaxDelayConstraint(TripConstraint):
    """Esclude treni con ritardo superiore a max_delay minuti"""
    def __init__(self, max_delay_minutes, **kwargs):
        super().__init__(**kwargs)
        self.max_delay = max_delay_minutes
        self.name = f"Ritardo massimo: {max_delay_minutes} minuti"
    
    def evaluate(self, solution):
        # Verifica che nessun treno abbia ritardo > max_delay
        return solution.get('ritardo', 0) <= self.max_delay


class TrainCategoryConstraint(TripConstraint):
    """Limita le categorie di treni accettabili"""
    def __init__(self, allowed_categories, **kwargs):
        super().__init__(**kwargs)
        self.allowed_categories = allowed_categories
        self.name = f"Categorie ammesse: {', '.join(allowed_categories)}"
    
    def evaluate(self, solution):
        categoria = solution.get('categoria', '')
        return categoria in self.allowed_categories


class DepartureTimeConstraint(TripConstraint):
    """Vincolo sull'orario di partenza"""
    def __init__(self, earliest_time, latest_time, **kwargs):
        super().__init__(**kwargs)
        self.earliest = earliest_time
        self.latest = latest_time
        self.name = f"Partenza tra {earliest_time.strftime('%H:%M')} e {latest_time.strftime('%H:%M')}"
    
    def evaluate(self, solution):
        orario_partenza = solution.get('orarioPartenza')
        if not orario_partenza:
            return False
        
        # Converti timestamp in datetime
        dt_partenza = datetime.fromtimestamp(orario_partenza / 1000)
        
        return self.earliest <= dt_partenza <= self.latest


class MaxTransfersConstraint(TripConstraint):
    """Limita il numero massimo di cambi"""
    def __init__(self, max_transfers, **kwargs):
        super().__init__(**kwargs)
        self.max_transfers = max_transfers
        self.name = f"Cambi massimi: {max_transfers}"
    
    def evaluate(self, solution):
        # Questo constraint va applicato alle soluzioni complete, non ai singoli treni
        cambi = solution.get('cambi', 0)
        return cambi <= self.max_transfers


class PreferFastTrainsConstraint(TripConstraint):
    """Preferisce treni alta velocità (soft constraint)"""
    def __init__(self, **kwargs):
        super().__init__(weight=0.5, is_hard=False, **kwargs)
        self.name = "Preferenza per Alta Velocità"
    
    def score(self, solution):
        categoria = solution.get('categoria', '')
        # FR (Frecciarossa) e FA (Frecciargento) hanno score alto
        if categoria in ['FR', 'FA', 'FB']:
            return 1.0
        elif categoria in ['IC', 'ICN']:
            return 0.6
        else:
            return 0.2


class SimpleTripPlanner:
    """Pianificatore di viaggi con constraint"""
    
    def __init__(self):
        self.api = apitr(decodeJson=True)
        self.constraints = []
    
    def add_constraint(self, constraint):
        """Aggiunge un constraint al planner"""
        self.constraints.append(constraint)
        print(f"✅ Constraint aggiunto: {constraint.name}")
    
    def find_departures(self, station_name, departure_time):
        """Trova tutti i treni in partenza da una stazione"""
        print(f"\n🔍 Ricerca treni da {station_name}...")
        
        # Ottieni codice stazione
        cod_stazione = self.api.getCodStazione(station_name)
        if not cod_stazione:
            print(f"❌ Stazione '{station_name}' non trovata")
            return []
        
        print(f"   Codice stazione: {cod_stazione}")
        
        # Ottieni partenze
        partenze = self.api.getPartenze(cod_stazione, departure_time)
        if not partenze:
            print("❌ Nessuna partenza trovata")
            return []
        
        print(f"   Trovati {len(partenze)} treni in partenza")
        return partenze
    
    def filter_by_constraints(self, trains):
        """Filtra i treni applicando tutti i constraint"""
        print(f"\n🔧 Applicazione constraint...")
        
        # Separa constraint hard e soft
        hard_constraints = [c for c in self.constraints if c.is_hard]
        soft_constraints = [c for c in self.constraints if not c.is_hard]
        
        # Applica constraint hard (must satisfy)
        valid_trains = []
        for train in trains:
            satisfies_all = True
            for constraint in hard_constraints:
                if not constraint.evaluate(train):
                    satisfies_all = False
                    break
            
            if satisfies_all:
                valid_trains.append(train)
        
        print(f"   Treni validi dopo constraint hard: {len(valid_trains)}/{len(trains)}")
        
        # Calcola score per constraint soft
        scored_trains = []
        for train in valid_trains:
            score = 0.0
            for constraint in soft_constraints:
                score += constraint.weight * constraint.score(train)
            
            scored_trains.append({
                'train': train,
                'score': score
            })
        
        # Ordina per score decrescente
        scored_trains.sort(key=lambda x: x['score'], reverse=True)
        
        return [st['train'] for st in scored_trains]
    
    def display_results(self, trains, max_results=5):
        """Mostra i risultati in formato leggibile"""
        print(f"\n" + "="*80)
        print(f"📊 RISULTATI - Top {min(max_results, len(trains))} treni")
        print("="*80)
        
        for i, train in enumerate(trains[:max_results], 1):
            print(f"\n{i}. Treno {train.get('categoria', 'N/A')} {train.get('numeroTreno', 'N/A')}")
            print(f"   Destinazione: {train.get('destinazione', 'N/A')}")
            
            # Orario
            orario_ts = train.get('orarioPartenza')
            if orario_ts:
                orario = datetime.fromtimestamp(orario_ts / 1000)
                print(f"   Partenza: {orario.strftime('%H:%M')}")
            
            # Ritardo
            ritardo = train.get('ritardo', 0)
            if ritardo > 0:
                print(f"   ⚠️  Ritardo: {ritardo} minuti")
            else:
                print(f"   ✅ In orario")
            
            # Binario
            binario = train.get('binarioEffettivoPartenzaDescrizione')
            if binario:
                print(f"   Binario: {binario}")
            
            # Tipo treno
            tipo = train.get('compTipologiaTreno', 'N/A')
            print(f"   Tipologia: {tipo.capitalize()}")
        
        print("\n" + "="*80)


def demo_scenario_1():
    """
    SCENARIO 1: Viaggio di lavoro Milano → Roma
    - Partenza tra le 7:00 e le 9:00
    - Solo treni alta velocità (FR)
    - Ritardo massimo 5 minuti
    """
    print("\n" + "🎯"*40)
    print("SCENARIO 1: Viaggio di Lavoro - Milano → Roma")
    print("🎯"*40)
    
    planner = SimpleTripPlanner()
    
    # Definisci constraint
    planner.add_constraint(
        DepartureTimeConstraint(
            earliest_time=datetime.now().replace(hour=7, minute=0),
            latest_time=datetime.now().replace(hour=9, minute=0),
            is_hard=True
        )
    )
    
    planner.add_constraint(
        TrainCategoryConstraint(
            allowed_categories=['FR', 'FA', 'FB'],  # Solo Frecce
            is_hard=True
        )
    )
    
    planner.add_constraint(
        MaxDelayConstraint(
            max_delay_minutes=5,
            is_hard=True
        )
    )
    
    # Cerca treni
    departure_time = datetime.now().replace(hour=8, minute=0)
    trains = planner.find_departures("MILANO CENTRALE", departure_time)
    
    # Applica constraint
    filtered_trains = planner.filter_by_constraints(trains)
    
    # Mostra risultati
    planner.display_results(filtered_trains)


def demo_scenario_2():
    """
    SCENARIO 2: Viaggio economico Milano → Verona
    - Qualsiasi categoria di treno
    - Ritardo massimo 15 minuti
    - Preferenza per treni veloci (soft)
    """
    print("\n" + "🎯"*40)
    print("SCENARIO 2: Viaggio Economico - Milano → Verona")
    print("🎯"*40)
    
    planner = SimpleTripPlanner()
    
    # Constraint più flessibili
    planner.add_constraint(
        MaxDelayConstraint(
            max_delay_minutes=15,
            is_hard=True
        )
    )
    
    planner.add_constraint(
        PreferFastTrainsConstraint()  # Soft constraint
    )
    
    # Cerca treni
    departure_time = datetime.now()
    trains = planner.find_departures("MILANO CENTRALE", departure_time)
    
    # Filtra solo quelli diretti a Verona
    trains_to_verona = [
        t for t in trains 
        if 'VERONA' in t.get('destinazione', '').upper()
    ]
    
    print(f"   Treni diretti a Verona: {len(trains_to_verona)}")
    
    # Applica constraint
    filtered_trains = planner.filter_by_constraints(trains_to_verona)
    
    # Mostra risultati
    planner.display_results(filtered_trains)


def demo_scenario_3():
    """
    SCENARIO 3: Analisi ritardi in tempo reale
    - Mostra tutti i treni indipendentemente dai ritardi
    - Statistiche sui ritardi
    """
    print("\n" + "🎯"*40)
    print("SCENARIO 3: Analisi Ritardi in Tempo Reale")
    print("🎯"*40)
    
    api = apitr(decodeJson=True)
    
    stazione = "MILANO CENTRALE"
    cod_stazione = api.getCodStazione(stazione)
    partenze = api.getPartenze(cod_stazione, datetime.now())
    
    print(f"\n📊 Analisi {len(partenze)} treni in partenza da {stazione}")
    
    # Statistiche
    treni_in_orario = sum(1 for t in partenze if t.get('ritardo', 0) == 0)
    treni_ritardo_leggero = sum(1 for t in partenze if 0 < t.get('ritardo', 0) <= 5)
    treni_ritardo_medio = sum(1 for t in partenze if 5 < t.get('ritardo', 0) <= 15)
    treni_ritardo_pesante = sum(1 for t in partenze if t.get('ritardo', 0) > 15)
    
    print(f"\n📈 STATISTICHE RITARDI:")
    print(f"   ✅ In orario: {treni_in_orario} ({treni_in_orario/len(partenze)*100:.1f}%)")
    print(f"   🟡 Ritardo leggero (1-5 min): {treni_ritardo_leggero} ({treni_ritardo_leggero/len(partenze)*100:.1f}%)")
    print(f"   🟠 Ritardo medio (6-15 min): {treni_ritardo_medio} ({treni_ritardo_medio/len(partenze)*100:.1f}%)")
    print(f"   🔴 Ritardo pesante (>15 min): {treni_ritardo_pesante} ({treni_ritardo_pesante/len(partenze)*100:.1f}%)")
    
    # Raggruppa per categoria
    categorie = {}
    for t in partenze:
        cat = t.get('categoria', 'N/A')
        if cat not in categorie:
            categorie[cat] = {'count': 0, 'ritardo_totale': 0}
        categorie[cat]['count'] += 1
        categorie[cat]['ritardo_totale'] += t.get('ritardo', 0)
    
    print(f"\n📊 RITARDO MEDIO PER CATEGORIA:")
    for cat, stats in sorted(categorie.items()):
        ritardo_medio = stats['ritardo_totale'] / stats['count']
        print(f"   {cat}: {ritardo_medio:.1f} minuti (su {stats['count']} treni)")


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Constraint-Based Train Trip Planner - Demo Pratico         ║
    ║  Software Engineering Project                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Esegui i vari scenari
        demo_scenario_1()
        
        input("\n\nPremi ENTER per continuare con lo Scenario 2...")
        demo_scenario_2()
        
        input("\n\nPremi ENTER per continuare con lo Scenario 3...")
        demo_scenario_3()
        
        print("\n✅ Demo completata con successo!")
        
    except Exception as e:
        print(f"\n❌ Errore durante l'esecuzione: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
