
import json
import math
import subprocess
import sys
from datetime import datetime, timedelta

# Percentuale di appartamenti extra da considerare (es: 20% in più)
EXTRA_APT_PERCENTAGE = 0.2  # 20% - valore di default

# Esegui cleaner_list.py per aggiornare i dati dei cleaner dal DB
def refresh_cleaner_list():
    try:
        print("Eseguo cleaner_list.py per aggiornare i dati dei cleaner dal DB...")
        subprocess.run(['python3', 'scripts/cleaner_list.py'], check=True)
        print("Dati cleaner aggiornati con successo.")
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di cleaner_list.py: {e}")
        raise

# Calcola il numero di cleaner necessari in base al numero di appartamenti
def calculate_cleaners_needed(apartments):
    num_apts = len(apartments)
    num_apts_extra = int(num_apts * (1 + EXTRA_APT_PERCENTAGE))
    avg_apt_per_cleaner = 3
    return math.ceil(num_apts_extra / avg_apt_per_cleaner)

# Seleziona i cleaner da utilizzare per la giornata
def select_cleaners(cleaners, num_needed, premium_apts, standard_apts):
    # Calcola il deficit di ore rispetto al contratto
    def contract_min_hours(contract_type):
        if contract_type == "A":
            return 20
        elif contract_type == "B":
            return 30
        elif contract_type == "C":
            return 40
        return 0

    for c in cleaners:
        c["deficit_hours"] = contract_min_hours(c.get("contract_type")) - c.get("counter_hours", 0)

    # Filtra cleaner attivi, disponibili, con meno di 6 giorni consecutivi
    eligible_cleaners = [
        c for c in cleaners if c["active"] and c["available"] and c["counter_days"] < 6
    ]

    # Se non bastano, aggiungi anche quelli con più giorni consecutivi
    if len(eligible_cleaners) < num_needed:
        extra_cleaners = [
            c for c in cleaners if c["active"] and c["available"] and c["counter_days"] >= 6
        ]
        eligible_cleaners += extra_cleaners

    # Ordina per deficit_hours decrescente (più lontani dal minimo), poi per counter_days crescente
    eligible_cleaners.sort(key=lambda c: (-c["deficit_hours"], c["counter_days"]))

    # Calcola il numero di cleaner premium e standard necessari
    total_apts = premium_apts + standard_apts
    if total_apts == 0:
        return []

    # Gli appartamenti premium richiedono OBBLIGATORIAMENTE cleaner premium
    # Calcola quanti cleaner premium servono basandosi su una media di 3 apt per cleaner
    # Ma considera che i premium potrebbero avere cleaning_time più lunghi
    if premium_apts > 0:
        # Almeno 1 cleaner premium, ma calcola in base al carico di lavoro
        min_premium_cleaners = max(1, math.ceil(premium_apts / 2.5))  # Più conservativo per premium
        print(f"📋 Appartamenti Premium: {premium_apts} → Cleaner Premium necessari: {min_premium_cleaners}")
    else:
        min_premium_cleaners = 0
        print(f"📋 Nessun appartamento Premium trovato")
    
    # Calcola cleaner standard necessari per gli appartamenti standard
    if standard_apts > 0:
        standard_cleaners_for_standard_apts = max(1, math.ceil(standard_apts / 3))
        print(f"📋 Appartamenti Standard: {standard_apts} → Cleaner Standard necessari: {standard_cleaners_for_standard_apts}")
    else:
        standard_cleaners_for_standard_apts = 0
        print(f"📋 Nessun appartamento Standard trovato")
    
    # Cleaner premium possono anche fare appartamenti standard se necessario
    total_cleaners_needed = min_premium_cleaners + standard_cleaners_for_standard_apts
    
    # Se abbiamo più cleaner necessari del previsto, aggiustiamo dando priorità ai premium
    if total_cleaners_needed > num_needed:
        print(f"⚠️ Cleaners calcolati ({total_cleaners_needed}) > cleaners stimati ({num_needed})")
        # Priorità assoluta agli appartamenti premium - manteniamo SEMPRE i cleaner premium necessari
        if min_premium_cleaners <= num_needed:
            standard_cleaners_for_standard_apts = max(0, num_needed - min_premium_cleaners)
            print(f"🔄 Ridotto cleaner standard a: {standard_cleaners_for_standard_apts}")
        else:
            print(f"🚨 ATTENZIONE: Servono {min_premium_cleaners} cleaner Premium ma budget è solo {num_needed}")
            # Comunque privilegiamo i premium anche se sforano il budget
            standard_cleaners_for_standard_apts = 0
    
    # Seleziona cleaner premium (almeno quelli necessari per apt premium)
    available_premium = [c for c in eligible_cleaners if c["role"].lower() == "premium"]
    premium_cleaners = available_premium[:min_premium_cleaners]
    
    # Se non ci sono abbastanza cleaner premium, avvisa
    if len(premium_cleaners) < min_premium_cleaners:
        print(f"⚠️ ATTENZIONE: Servono {min_premium_cleaners} cleaner Premium per {premium_apts} appartamenti Premium")
        print(f"⚠️ Disponibili solo {len(premium_cleaners)} cleaner Premium!")
    
    # Seleziona cleaner standard
    available_standard = [c for c in eligible_cleaners if c["role"].lower() == "standard"]
    standard_cleaners = available_standard[:standard_cleaners_for_standard_apts]
    
    # Se abbiamo ancora bisogno di cleaner e ci sono premium extra, li usiamo
    total_selected = len(premium_cleaners) + len(standard_cleaners)
    if total_selected < num_needed and len(available_premium) > len(premium_cleaners):
        extra_premium_needed = min(num_needed - total_selected, 
                                 len(available_premium) - len(premium_cleaners))
        extra_premium = available_premium[len(premium_cleaners):len(premium_cleaners) + extra_premium_needed]
        premium_cleaners.extend(extra_premium)

    selected_cleaners = premium_cleaners + standard_cleaners
    
    print(f"\n📊 RIEPILOGO SELEZIONE CLEANER:")
    print(f"🏆 Cleaner Premium selezionati: {len(premium_cleaners)} (per {premium_apts} apt premium)")
    print(f"👥 Cleaner Standard selezionati: {len(standard_cleaners)} (per {standard_apts} apt standard)")
    print(f"📈 Totale cleaner selezionati: {len(selected_cleaners)}")
    print(f"🎯 Target stimato: {num_needed}")
    
    # Verifica coverage appartamenti premium
    if premium_apts > 0:
        premium_coverage = len(premium_cleaners) * 2.5  # Stima appartamenti gestibili
        if premium_coverage >= premium_apts:
            print(f"✅ Coverage appartamenti Premium: OK ({premium_coverage:.1f} >= {premium_apts})")
        else:
            print(f"⚠️ Coverage appartamenti Premium: INSUFFICIENTE ({premium_coverage:.1f} < {premium_apts})")
    
    # Verifica availability cleaner premium
    total_premium_available = len([c for c in eligible_cleaners if c["role"].lower() == "premium"])
    if premium_apts > 0 and len(premium_cleaners) < min_premium_cleaners:
        print(f"🚨 ALERT: Mancano {min_premium_cleaners - len(premium_cleaners)} cleaner Premium!")
        print(f"   Disponibili totali Premium: {total_premium_available}")
    
    return selected_cleaners

# Salva i cleaner selezionati in un file JSON nella cartella data
def save_selected_cleaners(selected_cleaners, selected_date=None, total_apartments=0, extra_apartments=0, output_file="data/sel_cleaners.json"):
    # Se non viene fornita una data, usa quella di domani
    if selected_date is None:
        tomorrow = datetime.now() + timedelta(days=1)
        selected_date = tomorrow.strftime("%Y-%m-%d")
    
    # Carica i dati esistenti o crea una struttura vuota
    try:
        with open(output_file, "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {"dates": {}}
    
    # Assicurati che la struttura contenga la chiave "dates"
    if "dates" not in existing_data:
        existing_data = {"dates": {}}
    
    # Aggiorna i dati per la data specifica
    existing_data["dates"][selected_date] = {
        "timestamp": datetime.now().isoformat(),
        "cleaners": selected_cleaners,
        "total_selected": len(selected_cleaners),
        "total_available": 0,  # Sarà aggiornato dal web server se necessario
        "apartment_stats": {
            "total_apartments": total_apartments,
            "extra_apartments": extra_apartments,
            "percentage_used": EXTRA_APT_PERCENTAGE * 100
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(existing_data, f, indent=4)

# Funzione principale per selezionare i cleaner
def main():
    global EXTRA_APT_PERCENTAGE
    
    selected_date = None
    
    # Controlla i parametri della riga di comando
    if len(sys.argv) > 1:
        try:
            # Primo parametro: percentuale
            percentage = float(sys.argv[1])
            EXTRA_APT_PERCENTAGE = percentage / 100.0
            print(f"Usando percentuale custom: {percentage}%")
        except ValueError:
            print("Parametro percentuale non valido, uso valore di default")
    
    if len(sys.argv) > 2:
        # Secondo parametro: data
        selected_date = sys.argv[2]
        print(f"Usando data specifica: {selected_date}")
    
    # Aggiorna la lista dei cleaner dal DB
    refresh_cleaner_list()

    # Carica i dati dei cleaner
    with open("data/modello_cleaner.json") as f:
        cleaners = json.load(f)["cleaners"]

    # Carica gli appartamenti dalla data specifica
    with open("data/modello_apt.json") as f:
        apartments_data = json.load(f)
    
    # Usa la data specificata o cerca la data più recente per gli appartamenti
    if selected_date and "dates" in apartments_data and selected_date in apartments_data["dates"]:
        apartments = apartments_data["dates"][selected_date].get("apt", [])
        print(f"Usando appartamenti dalla data specifica: {selected_date}")
    elif "dates" in apartments_data and apartments_data["dates"]:
        latest_date = max(apartments_data["dates"].keys())
        apartments = apartments_data["dates"][latest_date].get("apt", [])
        print(f"Usando appartamenti dalla data più recente: {latest_date}")
    else:
        # Fallback al formato vecchio per compatibilità
        apartments = apartments_data.get("apt", [])
        print("Usando appartamenti dal formato compatibilità (senza date)")

    if not apartments:
        print("ATTENZIONE: Nessun appartamento trovato per la data selezionata!")
        print("Esegui prima task_selection.py per caricare gli appartamenti.")
        return

    # Log del numero di appartamenti da pulire
    total_apartments = len(apartments)
    extra_apartments = int(total_apartments * EXTRA_APT_PERCENTAGE)
    
    print(f"Numero totale di appartamenti da pulire: {total_apartments}")
    print(f"Appartamenti aggiuntivi stimati ({EXTRA_APT_PERCENTAGE*100}%): {extra_apartments}")

    # Conta appartamenti premium e standard
    premium_apts = len([apt for apt in apartments if apt["type"].lower() == "premium"])
    standard_apts = len([apt for apt in apartments if apt["type"].lower() == "standard"])

    print(f"Numero di appartamenti premium: {premium_apts}")
    print(f"Numero di appartamenti standard: {standard_apts}")

    # Calcola il numero di cleaner necessari
    num_needed = calculate_cleaners_needed(apartments)
    print(f"Numero stimato di cleaner necessari: {num_needed}")

    # Seleziona i cleaner
    selected_cleaners = select_cleaners(cleaners, num_needed, premium_apts, standard_apts)
    print(f"Cleaner selezionati: {len(selected_cleaners)}")

    # Salva i cleaner selezionati in un file JSON con statistiche
    save_selected_cleaners(selected_cleaners, selected_date, total_apartments, extra_apartments)

if __name__ == "__main__":
    main()
