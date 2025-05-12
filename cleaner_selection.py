import json
import math

# Calcola il numero di cleaner necessari in base al numero di appartamenti
def calculate_cleaners_needed(apartments):
    num_apts = len(apartments)
    avg_apt_per_cleaner = 3
    return math.ceil(num_apts / avg_apt_per_cleaner)

# Seleziona i cleaner da utilizzare per la giornata
def select_cleaners(cleaners, num_needed):
    # Ordina i cleaner per disponibilità o altri criteri (es. esperienza, ruolo, ecc.)
    # Qui si assume che i cleaner siano già ordinati per priorità nel file JSON
    selected_cleaners = cleaners[:num_needed]
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

    # Calcola il numero di cleaner necessari
    num_needed = calculate_cleaners_needed(apartments)
    print(f"Numero stimato di cleaner necessari: {num_needed}")

    # Seleziona i cleaner
    selected_cleaners = select_cleaners(cleaners, num_needed)
    print(f"Cleaner selezionati: {len(selected_cleaners)}")

    # Salva i cleaner selezionati in un file JSON
    save_selected_cleaners(selected_cleaners)

if __name__ == "__main__":
    main()