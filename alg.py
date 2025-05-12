import subprocess
import json
import math
from gmaps import calcola_distanza
from geopy.distance import geodesic

def run_dependency_scripts():
    subprocess.run(["python3", "cleaner_list.py"])
    subprocess.run(["python3", "task_selection.py"])


def load_data():
    with open("modello_cleaner.json") as f:
        cleaners = json.load(f)
    with open("modello_apt.json") as f:
        apartments = json.load(f)
    return cleaners, apartments


def calculate_cleaners_needed(apartments):
    # Separa gli apt premium e standard
    premium_apts = [a for a in apartments if a["type"].lower() == "premium"]
    standard_apts = [a for a in apartments if a["type"].lower() == "standard"]

    def estimate_cleaners(num_apt):
        # Preferiamo assegnare 4 apt per cleaner
        cleaners = num_apt // 4
        rest = num_apt % 4
        if rest > 0:
            cleaners += 1
        return cleaners

    n_premium_cleaners = estimate_cleaners(len(premium_apts))
    n_standard_cleaners = estimate_cleaners(len(standard_apts))

    return n_premium_cleaners, n_standard_cleaners


def filter_priority1_apts(apartments):
    return [a for a in apartments if a.get("checkin_time") == "14:00" or a.get("small_equipment") is True]


def assign_priority(cleaners, apartments, priority_level, previous_assignments):
    assignments = []
    cleaner_task_count = {cleaner["id"]: 0 for cleaner in cleaners}  # Traccia il numero di apt assegnati a ciascun cleaner

    # Filtra i cleaner disponibili per ruolo
    premium_cleaners = [cleaner for cleaner in cleaners if cleaner["role"] == "Premium"]
    standard_cleaners = [cleaner for cleaner in cleaners if cleaner["role"] == "Standard"]

    # Separiamo gli appartamenti premium e standard
    premium_apts = [apt for apt in apartments if apt["type"] == "Premium"]
    standard_apts = [apt for apt in apartments if apt["type"] == "Standard"]

    # Funzione per assegnare appartamenti in modo round-robin
    def distribute_apartments(apts, cleaners):
        cleaner_index = 0
        for apt in apts:
            # Trova il cleaner corrente
            cleaner = cleaners[cleaner_index]
            # Assegna l'appartamento al cleaner
            assignments.append({
                "cleaner_id": cleaner["id"],
                "apt_id": apt["task_id"],
                "priority": priority_level,
                "start_time": "08:00",  # Dummy
                "estimated_end": "09:00"  # Dummy
            })
            cleaner_task_count[cleaner["id"]] += 1  # Incrementa il conteggio degli apt assegnati al cleaner
            print(f"Assegnato appartamento {apt['task_id']} al cleaner {cleaner['id']} (Totale assegnati: {cleaner_task_count[cleaner['id']]})")

            # Passa al prossimo cleaner (ciclo round-robin)
            cleaner_index = (cleaner_index + 1) % len(cleaners)

    # Distribuisci gli appartamenti premium e standard
    if premium_cleaners:
        distribute_apartments(premium_apts, premium_cleaners)
    if standard_cleaners:
        distribute_apartments(standard_apts, standard_cleaners)

    return assignments


def find_closest_apt(cleaner_last_apt, remaining_apts):
    distances = []
    for apt in remaining_apts:
        distance_data = calcola_distanza(
            cleaner_last_apt["lat"], cleaner_last_apt["lng"],
            apt["lat"], apt["lng"]
        )
        if distance_data and "distanza_metri" in distance_data:
            distances.append((apt, distance_data["distanza_metri"]))
    distances.sort(key=lambda x: x[1])
    return distances[0][0] if distances else None

def calculate_travel_times(cleaner_last_apt, remaining_apts):
    travel_times = []
    for apt in remaining_apts:
        distance_data = calcola_distanza(
            cleaner_last_apt["lat"], cleaner_last_apt["lng"],
            apt["lat"], apt["lng"]
        )
        if distance_data and "durata" in distance_data:
            travel_times.append((apt, distance_data["durata"]))
    travel_times.sort(key=lambda x: x[1])  # Ordina per tempo di percorrenza
    return travel_times


def assign_by_distance(cleaners, apartments, existing_assignments):
    

    cleaner_task_count = {
        c["id"]: sum(1 for a in existing_assignments if a["cleaner_id"] == c["id"])
        for c in cleaners
    }

    available_apts = [a for a in apartments if a["task_id"] not in [x["apt_id"] for x in existing_assignments]]
    new_assignments = []

    for cleaner in cleaners:
        assigned_count = cleaner_task_count.get(cleaner["id"], 0)
        if assigned_count >= 4:
            continue

        cleaner_location = (cleaner["lat"], cleaner["lng"])

        # Ordina gli apt disponibili per distanza da questo cleaner
        sorted_apts = sorted(
            available_apts,
            key=lambda a: geodesic(cleaner_location, (a["lat"], a["lng"])).km
        )

        for apt in sorted_apts:
            if apt["task_id"] in [x["apt_id"] for x in new_assignments]:
                continue

            if assigned_count >= 4:
                break

            assigned_count += 1
            cleaner_task_count[cleaner["id"]] = assigned_count

            new_assignment = {
                "cleaner_id": cleaner["id"],
                "apt_id": apt["task_id"],
                "priority": assigned_count,
                "start_time": "09:00",  # puoi calcolare dinamicamente se vuoi
                "estimated_end": "10:00",
            }
            new_assignments.append(new_assignment)

    return new_assignments



def save_assignments(assignments):
    with open("assignments.json", "w") as f:
        json.dump(assignments, f, indent=4)


def main():

    # 1. Esegui gli script per generare i dati
    print("Eseguo task_selection.py...")
    subprocess.run(["python3", "task_selection.py"])
    
    print("Eseguo cleaner_list.py...")
    subprocess.run(["python3", "cleaner_list.py"])

    # 2. Carica i dati degli appartamenti
    with open("modello_apt.json") as f:
        apt_data = json.load(f)
        apartments = apt_data["apt"]

    # 3. Carica i dati dei cleaner
    with open("modello_cleaner.json") as f:
        cleaner_data = json.load(f)
        cleaners = []
        for c in cleaner_data["cleaners"]:
            c["id"] = f"{c['name'].strip()}_{c['lastname'].strip()}"
            cleaners.append(c)

    # 4. Calcola quanti cleaner servono
    n_premium, n_standard = calculate_cleaners_needed(apartments)
    print(f"Cleaners necessari - Premium: {n_premium}, Standard: {n_standard}")

    n_cleaners = n_premium + n_standard

    # 5. Filtra gli appartamenti di priorità 1
    priority1_apts = filter_priority1_apts(apartments)

    # 6. Assegna priorità 1 (una per cleaner)
    assignments = assign_priority(cleaners, priority1_apts, priority_level=1, previous_assignments=[])
    print(f"Appartamenti di priorità 1 assegnati: {len(assignments)}")

    # 7. Assegna priorità successive (2, 3, ...) in base alla distanza
    #priority = 2
    # ...
    all_assignments = assignments.copy()

    while True:
        remaining_apts = [a for a in apartments if a["task_id"] not in [x["apt_id"] for x in all_assignments]]
        if not remaining_apts:
            break

        next_batch = assign_by_distance(cleaners, apartments, existing_assignments=all_assignments)
        if not next_batch:
            break

        all_assignments.extend(next_batch)

    #priority += 1

    # 8. Salva le assegnazioni finali
    output = {"assignment": all_assignments}
    save_assignments(output)
    print("Assegnazioni completate e salvate in assignments.json.")

if __name__ == "__main__":
    main()