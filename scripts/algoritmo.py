import json
from gmaps import get_walk_time  # funzione esterna per ottenere tempo di cammino tra due indirizzi
from itertools import combinations
from datetime import timedelta


# ---- 1. PRIORITY RULES ----
def get_priority(apt):
    check_in = apt.get("check_in", "")
    small_equipment = apt.get("small_equipment", False)
    if check_in == "14:00" or small_equipment:
        return 1
    elif check_in == "15:00":
        return 2
    else:
        return 3


# ---- 2. LOAD DATA ----
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def time_between_apartments(apt1, apt2):
    result = calcola_distanza(
        apt1["lat"], apt1["lng"],
        apt2["lat"], apt2["lng"],
        mode="walking"
    )
    if result is None:
        return float("inf")  # Scarta coppie non calcolabili
    return result["durata"]  # in secondi


# ---- 3. CLEANER ASSIGNMENT LOGIC ----
def build_assignments(cleaners, apartments, sel_cleaners):
    # Filtra i cleaners selezionati
    cleaners = [c for c in cleaners if c["id"] in sel_cleaners]
    
    # Aggiungi priorità agli apt
    for apt in apartments:
        apt["priority"] = get_priority(apt)
    
    # Ordina appartamenti per priorità crescente
    apartments.sort(key=lambda a: a["priority"])
    
    # Appartamenti non ancora assegnati
    unassigned_apts = apartments[:]
    assignments = []
    
    for cleaner in cleaners:
        cleaner_id = cleaner["id"]
    
        for apt in unassigned_apts[:]:  # copia
            if apt.get("assigned", False):
                continue
    
            current_pack = [apt]
            walk_total_min = 0
            clean_total = apt.get("cleaning_time", 60)  # default 60 minuti
    
            for candidate in unassigned_apts:
                if candidate == apt or candidate.get("assigned", False):
                    continue
    
                # Calcola tempo di percorrenza a piedi in secondi e converti in minuti
                walk_time_sec = time_between_apartments(current_pack[-1], candidate)
                walk_time_min = walk_time_sec / 60 if walk_time_sec != float("inf") else float("inf")
    
                potential_clean_time = candidate.get("cleaning_time", 60)
    
                if walk_time_min <= 15 and clean_total + potential_clean_time + walk_total_min + walk_time_min <= 240:
                    current_pack.append(candidate)
                    clean_total += potential_clean_time
                    walk_total_min += walk_time_min
    
            # Segna come assegnati
            for ap in current_pack:
                ap["assigned"] = True
    
            # Salva pacchetto
            assignments.append({
                "cleaner_id": cleaner_id,
                "cleaner_name": cleaner["name"],
                "apartments": [{"apt_id": a["id"], "address": a["address"]} for a in current_pack],
                "priority_levels": [a["priority"] for a in current_pack],
                "total_cleaning_time_min": clean_total,
                "total_walk_time_min": int(round(walk_total_min)),
                "zone": cleaner.get("zone", "N/D")
            })
    
        # Rimuove apt assegnati da unassigned_apts
        unassigned_apts = [a for a in unassigned_apts if not a.get("assigned", False)]
    
    # Se rimangono apt non assegnati (es. > 4h), assegnali singolarmente
    if unassigned_apts:
        for apt in unassigned_apts:
            closest_cleaner = min(cleaners, key=lambda c: time_between_apartments(c, apt))
    
            walk_time_sec = time_between_apartments(closest_cleaner, apt)
            walk_time_min = walk_time_sec / 60 if walk_time_sec != float("inf") else 0
    
            assignments.append({
                "cleaner_id": closest_cleaner["id"],
                "cleaner_name": closest_cleaner["name"],
                "apartments": [{"apt_id": apt["id"], "address": apt["address"]}],
                "priority_levels": [apt["priority"]],
                "total_cleaning_time_min": apt.get("cleaning_time", 60),
                "total_walk_time_min": int(round(walk_time_min)),
                "zone": closest_cleaner.get("zone", "N/D")
            })

    return assignments



# ---- 4. MAIN ----
def main(selected_date=None):
    import sys
    
    # Se viene passata una data come parametro da linea di comando
    if len(sys.argv) > 1:
        selected_date = sys.argv[1]
    
    # Carica i dati dal nuovo formato con date
    sel_cleaners_data = load_json("data/sel_cleaners.json")
    
    # Usa la data specificata o cerca la data più recente
    if selected_date and "dates" in sel_cleaners_data and selected_date in sel_cleaners_data["dates"]:
        cleaners = sel_cleaners_data["dates"][selected_date].get("cleaners", [])
        print(f"Usando cleaners dalla data specifica: {selected_date}")
    elif "dates" in sel_cleaners_data and sel_cleaners_data["dates"]:
        latest_date = max(sel_cleaners_data["dates"].keys())
        cleaners = sel_cleaners_data["dates"][latest_date].get("cleaners", [])
        print(f"Usando cleaners dalla data più recente: {latest_date}")
    else:
        print("Nessun cleaner trovato nel file sel_cleaners.json")
        cleaners = []
    
    apartments_data = load_json("data/modello_apt.json")
    apartments = apartments_data.get("apt", [])

    if not cleaners:
        print("Errore: Nessun cleaner selezionato trovato!")
        return

    assignments = build_assignments(cleaners, apartments, [c["id"] for c in cleaners])

    with open("data/assignments.json", "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)

    print(f"Assegnazioni completate. Totale pacchetti: {len(assignments)}")



if __name__ == "__main__":
    main()
