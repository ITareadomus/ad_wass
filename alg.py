import subprocess
import json
import math

# Vengono reperiti i cleaners disponibili e gli appartamenti da pulire
def run_dependency_scripts():
    subprocess.run(["python3", "task_selection.py"])
    subprocess.run(["python3", "cleaner_list.py"])

# Carica i dati dei cleaners e degli appartamenti dai file JSON
def load_data():
    with open("modello_cleaner.json") as f:
        cleaners_data = json.load(f)["cleaners"]
        cleaners = cleaners_data  # NON toccare cleaner["id"]!

    with open("modello_apt.json") as f:
        apartments = json.load(f)["apt"]

    return cleaners, apartments

    return cleaners, apartments

# Ci calcoliamo il numero di cleaners necessari in base al numero di appartamenti
def calculate_cleaners_needed(apartments):
    num_apts = len(apartments)
    avg_apt_per_cleaner = 3
    return math.ceil(num_apts / avg_apt_per_cleaner)


def filter_priority1_apts(apartments):
    return [a for a in apartments if a.get("checkin_time") == "14:00" or a.get("small_equipment") is True]



def assign_apartments(cleaners, apartments, max_apt_per_cleaner=3):
    assignments = []
    cleaner_task_count = {c["id"]: 0 for c in cleaners}
    assigned_apt_ids = set()

    priority1_apts = filter_priority1_apts(apartments)

    for apt in priority1_apts:
        for cleaner in cleaners:
            if cleaner["role"] == apt["type"] and cleaner_task_count[cleaner["id"]] < max_apt_per_cleaner:
                priority = cleaner_task_count[cleaner["id"]] + 1
                assignments.append({
                    "cleaner_id": cleaner["id"],  # deve essere il numero (es. 18)
                    "name": cleaner["name"],
                    "lastname": cleaner["lastname"],
                    "apt_id": apt["task_id"],
                    "priority": priority
                })
                cleaner_task_count[cleaner["id"]] += 1
                assigned_apt_ids.add(apt["task_id"])
                break

    remaining_apts = [a for a in apartments if a["task_id"] not in assigned_apt_ids]

    for apt in remaining_apts:
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

    return assignments



def save_assignments(assignments):
    with open("assignments.json", "w") as f:
        json.dump({"assignment": assignments}, f, indent=4)


def main():
    print("Lancio script di preparazione dati...")
    run_dependency_scripts()

    print("Carico dati...")
    cleaners, apartments = load_data()

    print(f"Totale appartamenti da pulire: {len(apartments)}")
    n_cleaners = calculate_cleaners_needed(apartments)
    print(f"Cleaners necessari (stima): {n_cleaners}")

    print("Assegno appartamenti ai cleaner...")
    assignments = assign_apartments(cleaners, apartments)

    save_assignments(assignments)
    print(f"Assegnazioni completate ({len(assignments)} assegnazioni). Salvate in 'assignments.json'.")


if __name__ == "__main__":
    main()
