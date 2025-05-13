import json
import math

# Calcola il numero di cleaner necessari in base al numero di appartamenti
def calculate_cleaners_needed(apartments):
    num_apts = len(apartments)
    avg_apt_per_cleaner = 3
    return math.ceil(num_apts / avg_apt_per_cleaner)

# Seleziona i cleaner da utilizzare per la giornata
def select_cleaners(cleaners, num_needed, premium_apts, standard_apts):
    # Filtra i cleaner attivi e disponibili
    eligible_cleaners = [
        c for c in cleaners if c["active"] and c["available"] and c["counter_days"] < 12
    ]

    # Ordina i cleaner per counter_hours (priorità a chi ha meno ore)
    eligible_cleaners.sort(key=lambda c: c["counter_hours"])

    # Calcola il numero di cleaner premium e standard necessari
    total_apts = premium_apts + standard_apts
    if total_apts == 0:
        return []  # Nessun appartamento da pulire

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

    # Combina i cleaner selezionati
    selected_cleaners = premium_cleaners + standard_cleaners
    return selected_cleaners

# Salva i cleaner selezionati in un file JSON
def save_selected_cleaners(selected_cleaners, output_file="sel_cleaners.json"):
    with open(output_file, "w") as f:
        json.dump({"cleaners": selected_cleaners}, f, indent=4)

# Funzione principale per selezionare i cleaner
def main():
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