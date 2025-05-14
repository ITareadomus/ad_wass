import subprocess
import json
from gmaps import calcola_distanza  # Importa la funzione per calcolare la distanza

# Esegui cleaner_selection.py per aggiornare la lista dei cleaner
def refresh_cleaner_selection():
    try:
        print("Eseguo cleaner_selection.py per aggiornare la lista dei cleaner...")
        subprocess.run(["python3", "cleaner_selection.py"], check=True)
        print("Lista dei cleaner aggiornata con successo.")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di cleaner_selection.py: {e}")
        raise

def refresh_task_selection():
    try:
        print("Eseguo task_selection.py per aggiornare la lista degli appartamenti...")
        subprocess.run(["python3", "task_selection.py"], check=True)
        print("Lista degli appartamenti aggiornata con successo.")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di task_selection.py: {e}")
        raise

# Carica i cleaner selezionati dal file JSON
def load_selected_cleaners():
    with open("sel_cleaners.json") as f:  # Cambiato il nome del file
        return json.load(f)["cleaners"]

# Carica i dati degli appartamenti dai file JSON
def load_apartments():
    with open("modello_apt.json") as f:
        apartments = json.load(f)["apt"]
    return apartments

def filter_priority1_apts(apartments):
    return [a for a in apartments if a.get("checkin_time") == "14:00" or a.get("small_equipment") is True]

def assign_apartments(cleaners, apartments, max_apt_per_cleaner=3):
    assignments = []
    cleaner_task_count = {c["id"]: 0 for c in cleaners}
    assigned_apt_ids = set()

    priority1_apts = filter_priority1_apts(apartments)

    # Funzione per trovare l'appartamento più adeguato
    def find_best_next_apartment(current_apt, remaining_apts):
        best_apt = None
        best_score = float('inf')

        for apt in remaining_apts:
            if apt["task_id"] in assigned_apt_ids:
                continue

            # Calcola la distanza tra l'appartamento corrente e quello candidato
            distanza = calcola_distanza(
                float(current_apt["lat"]), float(current_apt["lng"]),
                float(apt["lat"]), float(apt["lng"])
            )




            if not distanza:
                continue


            # Calcola un punteggio basato su distanza e orario
            distanza_metri = distanza["distanza_metri"]
            checkin_time = apt.get("checkin_time", "15:00") or "15:00"  # Default a "15:00" se checkin_time è null o None
            checkout_time = current_apt.get("checkout_time", "00:00") or "00:00"  # Default a mezzanotte se checkout_time è null o None

            try:
                orario_diff = abs(
                    int(checkin_time[:2]) - int(checkout_time[:2])
                )
            except ValueError:
                # Gestione di eventuali valori non validi
                orario_diff = float('inf')

            score = distanza_metri + (orario_diff * 100)  # Peso maggiore per la distanza


            if score < best_score:
                best_score = score
                best_apt = apt

        return best_apt

    # Assegna appartamenti con priorità 1
    for apt in priority1_apts:
        for cleaner in cleaners:
            if cleaner["role"] == apt["type"] and cleaner_task_count[cleaner["id"]] < max_apt_per_cleaner:
                priority = cleaner_task_count[cleaner["id"]] + 1
                assignments.append({
                    "cleaner_id": cleaner["id"],
                    "name": cleaner["name"],
                    "lastname": cleaner["lastname"],
                    "apt_id": apt["task_id"],
                    "priority": priority
                })
                cleaner_task_count[cleaner["id"]] += 1
                assigned_apt_ids.add(apt["task_id"])
                break

    # Assegna gli appartamenti rimanenti
    for cleaner in cleaners:
        current_apt = None
        for _ in range(max_apt_per_cleaner - cleaner_task_count[cleaner["id"]]):
            remaining_apts = [a for a in apartments if a["task_id"] not in assigned_apt_ids]

            if not remaining_apts:
                break

            if current_apt is None:
                # Se non c'è un appartamento corrente, assegna il primo disponibile
                next_apt = next((a for a in remaining_apts if cleaner["role"] == a["type"]), None)
            else:
                # Trova il prossimo appartamento migliore
                next_apt = find_best_next_apartment(current_apt, remaining_apts)

            if next_apt:
                priority = cleaner_task_count[cleaner["id"]] + 1
                assignments.append({
                    "cleaner_id": cleaner["id"],
                    "name": cleaner["name"],
                    "lastname": cleaner["lastname"],
                    "apt_id": next_apt["task_id"],
                    "priority": priority
                })
                cleaner_task_count[cleaner["id"]] += 1
                assigned_apt_ids.add(next_apt["task_id"])
                current_apt = next_apt

    return assignments

def save_assignments(assignments):
    with open("assignments.json", "w") as f:
        json.dump({"assignment": assignments}, f, indent=4)

def main():
    # Aggiorna la lista degli appartamenti e dei cleaner PRIMA di tutto
    refresh_task_selection()
    refresh_cleaner_selection()
    
    print("Carico cleaner selezionati...")
    cleaners = load_selected_cleaners()

    print("Carico dati degli appartamenti...")
    apartments = load_apartments()

    print(f"Totale appartamenti da pulire: {len(apartments)}")

    print("Assegno appartamenti ai cleaner...")
    assignments = assign_apartments(cleaners, apartments)

    save_assignments(assignments)
    print(f"Assegnazioni completate ({len(assignments)} assegnazioni). Salvate in 'assignments.json'.")

if __name__ == "__main__":
    main()