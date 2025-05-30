import json
import math
import subprocess

# Percentuale di appartamenti extra da considerare (es: 20% in più)
EXTRA_APT_PERCENTAGE = 0.2  # 20%

# Esegui cleaner_list.py per aggiornare i dati dei cleaner dal DB
def refresh_cleaner_list():
    try:
        print("Eseguo cleaner_list.py per aggiornare i dati dei cleaner dal DB...")
        subprocess.run(['python3', 'cleaner_list.py'], check=True)
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

    premium_ratio = premium_apts / total_apts
    num_premium_needed = round(num_needed * premium_ratio)
    num_standard_needed = num_needed - num_premium_needed

    # Seleziona cleaner premium
    premium_cleaners = [
        c for c in eligible_cleaners if c["role"].lower() == "premium"
    ][:num_premium_needed]

    # Seleziona cleaner standard
    standard_cleaners = [
        c for c in eligible_cleaners if c["role"].lower() == "standard"
    ][:num_standard_needed]

    selected_cleaners = premium_cleaners + standard_cleaners
    return selected_cleaners

# Salva i cleaner selezionati in un file JSON
def save_selected_cleaners(selected_cleaners, output_file="sel_cleaners.json"):
    with open(output_file, "w") as f:
        json.dump({"cleaners": selected_cleaners}, f, indent=4)

# Funzione principale per selezionare i cleaner
def main():
    # Aggiorna la lista dei cleaner dal DB
    refresh_cleaner_list()

    # Carica i dati dei cleaner e degli appartamenti
    with open("modello_cleaner.json") as f:
        cleaners = json.load(f)["cleaners"]

    with open("modello_apt.json") as f:
        apartments = json.load(f)["apt"]

    # Log del numero di appartamenti da pulire
    print(f"Numero totale di appartamenti da pulire: {len(apartments)}")

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

    # Salva i cleaner selezionati in un file JSON
    save_selected_cleaners(selected_cleaners)

if __name__ == "__main__":
    main()