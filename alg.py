from math import radians, sin, cos, sqrt, atan2

# Funzione per calcolare distanza Haversine (in km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Raggio della Terra in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# Funzione per calcolare la priorità di un appartamento
def calculate_priority(apt):
    reference_lat = 45.4342758
    reference_lng = 9.1739564

    checkin_time = apt.get("checkin_time")
    if checkin_time:
        try:
            hour, minute = map(int, checkin_time.split(":"))
            diff_from_14 = abs((hour * 60 + minute) - (14 * 60))  # distanza da 14:00 in minuti
        except:
            diff_from_14 = float('inf')
    else:
        diff_from_14 = float('inf')  # nessun orario = bassa priorità

    try:
        distance = haversine(reference_lat, reference_lng, float(apt["lat"]), float(apt["lng"]))
    except:
        distance = float('inf')

    return (diff_from_14, distance)

# Ordiniamo gli appartamenti
tasks_for_tomorrow_sorted = sorted(tasks_for_tomorrow, key=calculate_priority)

# Stampiamo il risultato
print("\n🏅 Appartamenti ordinati per priorità:")
for i, apt in enumerate(tasks_for_tomorrow_sorted, start=1):
    print(f"{i}. Task ID {apt['task_id']}, check-in: {apt.get('checkin_time')}, tipo: {apt['type']}")



# 1. Carichiamo i cleaner dal file JSON
with open("modello_cleaners.json", "r") as f:
    all_cleaners = json.load(f)

# 2. Filtriamo solo i cleaner disponibili
available_cleaners = [c for c in all_cleaners if c.get("available") is True]

# 3. Dividiamo per ruolo
premium_cleaners = [c for c in available_cleaners if c.get("role") == "Premium"]
standard_cleaners = [c for c in available_cleaners if c.get("role") == "Standard"]

# 4. Ordiniamo per ranking (priorità più alta = numero più basso)
premium_cleaners_sorted = sorted(premium_cleaners, key=lambda c: c.get("ranking", 9999))
standard_cleaners_sorted = sorted(standard_cleaners, key=lambda c: c.get("ranking", 9999))

# Stampiamo per verifica
print("\n👑 Premium cleaners:")
for c in premium_cleaners_sorted:
    print(f"- {c['name']} {c['lastname']}, ranking: {c['ranking']}")

print("\n🧹 Standard cleaners:")
for c in standard_cleaners_sorted:
    print(f"- {c['name']} {c['lastname']}, ranking: {c['ranking']}")



# Impostiamo un massimo di appartamenti per cleaner
MAX_TASKS_PER_CLEANER = 4

# Inizializziamo i dizionari con i task assegnati
assignments = {}

# Funzione di supporto per assegnare
def assign_tasks(cleaners, tasks, apt_type):
    for task in tasks:
        if task["type"] != apt_type:
            continue
        assigned = False
        for cleaner in cleaners:
            cid = f"{cleaner['name']} {cleaner['lastname']}"
            if cid not in assignments:
                assignments[cid] = []
            if len(assignments[cid]) < MAX_TASKS_PER_CLEANER:
                assignments[cid].append(task)
                assigned = True
                break
        if not assigned:
            print(f"⚠️ Nessun cleaner disponibile per task ID {task['task_id']} ({apt_type})")

# Prima assegnamo gli standard
assign_tasks(standard_cleaners_sorted, tasks_for_tomorrow_sorted, "Standard")

# Poi assegnamo i premium
assign_tasks(premium_cleaners_sorted, tasks_for_tomorrow_sorted, "Premium")

# Stampiamo il risultato finale
print("\n📦 Assegnazioni finali:")
for cleaner, tasks in assignments.items():
    print(f"\n🧑‍💼 {cleaner}:")
    for i, task in enumerate(tasks, start=1):
        print(f"  {i}. Task ID {task['task_id']} - Check-in: {task.get('checkin_time')}, Tipo: {task['type']}")
