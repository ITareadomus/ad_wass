import json
from datetime import datetime
from collections import defaultdict

# --- Funzioni ---
def checkin_priority(checkin_time_str):
    if not checkin_time_str:
        return float('inf')
    try:
        t = datetime.strptime(checkin_time_str, "%H:%M").time()
        return abs(t.hour + t.minute / 60 - 14)
    except:
        return float('inf')

def assign_tasks(cleaners, tasks):
    assignments = defaultdict(list)
    cleaner_index = 0
    cleaners = [c for c in cleaners if c["available"]]
    if not cleaners:
        return assignments

    tasks_sorted = sorted(tasks, key=lambda t: checkin_priority(t.get("checkin_time")))

    for task in tasks_sorted:
        cleaner = cleaners[cleaner_index]
        assignments[cleaner["name"] + " " + cleaner["lastname"]].append(task)
        cleaner_index = (cleaner_index + 1) % len(cleaners)

    return assignments

def format_assignment(cleaner_name, tasks):
    formatted = []
    for i, task in enumerate(tasks, start=1):
        formatted.append({
            "cleaner": cleaner_name,
            "task_id": task["task_id"],
            "structure_id": task["structure_id"],
            "address": task["address"],
            "checkin_time": task.get("checkin_time"),
            "priority": i
        })
    return formatted

# --- Caricamento dati da file ---
with open("modello_cleaner.json", "r") as f:
    cleaners = json.load(f)

with open("modello_apt.json", "r") as f:
    tasks = json.load(f)

# --- Separazione ---
premium_cleaners = [c for c in cleaners if c["role"] == "Premium" and c["available"]]
standard_cleaners = [c for c in cleaners if c["role"] == "Standard" and c["available"]]

premium_tasks = [t for t in tasks if t["type"] == "Premium"]
standard_tasks = [t for t in tasks if t["type"] == "Standard"]

# --- Assegnazioni ---
premium_assignments = assign_tasks(premium_cleaners, premium_tasks)
standard_assignments = assign_tasks(standard_cleaners, standard_tasks)

# --- Unione e output ---
final_assignments = []
for cleaner_name, task_list in premium_assignments.items():
    final_assignments.extend(format_assignment(cleaner_name, task_list))

for cleaner_name, task_list in standard_assignments.items():
    final_assignments.extend(format_assignment(cleaner_name, task_list))

# --- Salva in un nuovo file o stampa ---
with open("assegnazioni_finali.json", "w") as f:
    json.dump(final_assignments, f, indent=2)

print("✅ Assegnazioni salvate in 'assegnazioni_finali.json'")

