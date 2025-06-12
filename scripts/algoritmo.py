import json
import sys
from datetime import datetime
import math

def haversine_distance(lat1, lng1, lat2, lng2):
    """
    Calcola la distanza in metri tra due punti usando la formula di Haversine
    """
    R = 6371000  # Raggio della Terra in metri

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def calcola_distanza(lat1, lng1, lat2, lng2, mode="walking"):
    """
    Calcola tempo di percorrenza tra due punti
    """
    try:
        lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
        distance_m = haversine_distance(lat1, lng1, lat2, lng2)

        # Velocità media a piedi: 5 km/h = 1.39 m/s
        speed_ms = 1.39
        time_seconds = distance_m / speed_ms

        return {
            "durata": time_seconds,
            "distanza": distance_m
        }
    except:
        return None

def get_priority(apt):
    """Calcola priorità appartamento"""
    checkin_time = apt.get("checkin_time", "")
    small_equipment = apt.get("small_equipment", False)

    if checkin_time == "14:00" or small_equipment:
        return 1
    elif checkin_time == "15:00":
        return 2
    else:
        return 3

def load_json(path):
    """Carica file JSON"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def time_between_apartments(apt1, apt2):
    """Calcola tempo tra due appartamenti"""
    if not apt1.get("lat") or not apt1.get("lng") or not apt2.get("lat") or not apt2.get("lng"):
        return float("inf")

    result = calcola_distanza(
        apt1["lat"], apt1["lng"],
        apt2["lat"], apt2["lng"],
        mode="walking"
    )

    if result is None:
        return float("inf")
    return result["durata"]  # in secondi

def build_assignments(cleaners, apartments):
    """Costruisce le assegnazioni"""
    print(f"Appartamenti da assegnare: {len(apartments)}")

    if not apartments:
        print("❌ Nessun appartamento trovato!")
        return []

    # Aggiungi priorità agli appartamenti
    for apt in apartments:
        apt["priority"] = get_priority(apt)
        apt["assigned"] = False

    # Ordina appartamenti per priorità crescente
    apartments.sort(key=lambda a: a["priority"])

    assignments = []

    for cleaner in cleaners:
        if not cleaner.get("available", True):
            continue

        cleaner_id = cleaner["id"]
        cleaner_name = cleaner.get("name", "")
        cleaner_lastname = cleaner.get("lastname", "")
        cleaner_role = cleaner.get("role", "Standard")

        # Trova appartamenti non assegnati compatibili con il ruolo del cleaner
        if cleaner_role.lower() == "premium":
            # I cleaner premium possono pulire sia premium che standard
            unassigned_apts = [apt for apt in apartments if not apt.get("assigned", False)]
            # Ma prioritizziamo quelli premium
            premium_apts = [apt for apt in unassigned_apts if apt.get("type", "Standard").lower() == "premium"]
            standard_apts = [apt for apt in unassigned_apts if apt.get("type", "Standard").lower() == "standard"]
            unassigned_apts = premium_apts + standard_apts
        else:
            # I cleaner standard possono pulire SOLO appartamenti standard
            unassigned_apts = [apt for apt in apartments 
                             if not apt.get("assigned", False) 
                             and apt.get("type", "Standard").lower() == "standard"]

        if not unassigned_apts:
            print(f"⚠️ Nessun appartamento compatibile per {cleaner_name} {cleaner_lastname} ({cleaner_role})")
            continue

        # Prendi il primo appartamento disponibile
        current_apt = unassigned_apts[0]
        current_pack = [current_apt]
        current_apt["assigned"] = True

        walk_total_sec = 0
        clean_total_min = current_apt.get("cleaning_time", 60) or 60

        # Cerca appartamenti vicini (PRIMO PASSAGGIO: max 3 appartamenti)
        for candidate in unassigned_apts[1:]:
            if candidate.get("assigned", False):
                continue

            # Limita a 3 appartamenti nel primo passaggio
            if len(current_pack) >= 3:
                break

            # Calcola tempo di percorrenza
            walk_time_sec = time_between_apartments(current_pack[-1], candidate)
            walk_time_min = walk_time_sec / 60 if walk_time_sec != float("inf") else float("inf")

            potential_clean_time = candidate.get("cleaning_time", 60) or 60

            # Verifica se può essere aggiunto (max 20 min di cammino)
            if walk_time_min <= 20:
                current_pack.append(candidate)
                candidate["assigned"] = True
                clean_total_min += potential_clean_time
                walk_total_sec += walk_time_sec

        # Crea i dettagli della sequenza nel formato atteso dalle maschere
        sequence_details = []
        for i, apt in enumerate(current_pack):
            sequence_details.append({
                "task_id": apt.get("structure_id") or apt.get("task_id", "N/A"),
                "structure_id": apt.get("structure_id"),
                "address": apt.get("address", "Indirizzo non disponibile"),
                "lat": str(apt.get("lat", "")),
                "lng": str(apt.get("lng", "")),
                "type": apt.get("type", "Standard"),
                "priority": i + 1,  # Sequenza nell'ordine di visita
                "checkin_time": apt.get("checkin_time"),
                "checkout_time": apt.get("checkout_time"),
                "cleaning_time": apt.get("cleaning_time", 60)
            })

        # Crea l'assegnazione nel formato atteso dalle maschere
        assignment = {
            "cleaner_id": cleaner_id,
            "name": cleaner_name,
            "lastname": cleaner_lastname,
            "role": cleaner_role,
            "sequence_details": sequence_details,
            "total_apartments": len(current_pack),
            "total_cleaning_time_min": clean_total_min,
            "total_walk_time_min": int(round(walk_total_sec / 60)),
            "priority_levels": [apt["priority"] for apt in current_pack]
        }

        assignments.append(assignment)
        print(f"Assegnato a {cleaner_name} {cleaner_lastname}: {len(current_pack)} appartamenti")

    # SECONDO PASSAGGIO: Assegna appartamenti rimanenti al cleaner più vicino
    unassigned_remaining = [apt for apt in apartments if not apt.get("assigned", False)]
    if unassigned_remaining and assignments:
        print(f"\n🔄 SECONDO PASSAGGIO: {len(unassigned_remaining)} appartamenti non assegnati")
        
        for apt in unassigned_remaining:
            best_assignment = None
            best_cleaner_idx = -1
            min_distance = float('inf')
            
            # Trova il cleaner con l'appartamento più vicino a questo appartamento non assegnato
            for idx, assignment in enumerate(assignments):
                cleaner_role = assignment["role"]
                
                # Verifica compatibilità ruolo
                apt_type = apt.get("type", "Standard").lower()
                if cleaner_role.lower() == "standard" and apt_type == "premium":
                    continue  # Cleaner standard non può fare apt premium
                
                # Calcola la distanza minima da qualsiasi appartamento già assegnato a questo cleaner
                for assigned_apt in assignment["sequence_details"]:
                    if assigned_apt.get("lat") and assigned_apt.get("lng"):
                        distance = time_between_apartments(apt, {
                            "lat": assigned_apt["lat"], 
                            "lng": assigned_apt["lng"]
                        })
                        if distance < min_distance:
                            min_distance = distance
                            best_assignment = assignment
                            best_cleaner_idx = idx
            
            # Assegna all'assignment più vicino
            if best_assignment and min_distance != float('inf'):
                apt["assigned"] = True
                
                # Aggiungi alla sequenza
                new_priority = len(best_assignment["sequence_details"]) + 1
                best_assignment["sequence_details"].append({
                    "task_id": apt.get("structure_id") or apt.get("task_id", "N/A"),
                    "structure_id": apt.get("structure_id"),
                    "address": apt.get("address", "Indirizzo non disponibile"),
                    "lat": str(apt.get("lat", "")),
                    "lng": str(apt.get("lng", "")),
                    "type": apt.get("type", "Standard"),
                    "priority": new_priority,
                    "checkin_time": apt.get("checkin_time"),
                    "checkout_time": apt.get("checkout_time"),
                    "cleaning_time": apt.get("cleaning_time", 60)
                })
                
                # Aggiorna statistiche
                best_assignment["total_apartments"] += 1
                best_assignment["total_cleaning_time_min"] += apt.get("cleaning_time", 60) or 60
                walk_time_min = min_distance / 60 if min_distance != float("inf") else 5
                best_assignment["total_walk_time_min"] += int(walk_time_min)
                
                print(f"    ✅ Appartamento {apt.get('task_id')} assegnato a {best_assignment['name']} {best_assignment['lastname']} (distanza: {walk_time_min:.1f} min)")
            else:
                print(f"    ❌ Impossibile assegnare appartamento {apt.get('task_id')} - nessun cleaner compatibile trovato")

    # Statistiche finali
    total_assigned = sum(a["total_apartments"] for a in assignments)
    total_original = len(apartments)
    unassigned_final = [apt for apt in apartments if not apt.get("assigned", False)]
    
    print(f"\n📊 STATISTICHE FINALI:")
    print(f"  🏠 Appartamenti con coordinate: {total_original}")
    print(f"  ✅ Appartamenti assegnati: {total_assigned}")
    print(f"  ❌ Appartamenti NON assegnati: {len(unassigned_final)}")
    print(f"  📈 Percentuale assegnazione: {(total_assigned/total_original)*100:.1f}%")
    
    if unassigned_final:
        print(f"\n⚠️ APPARTAMENTI NON ASSEGNATI:")
        for apt in unassigned_final[:5]:  # Mostra primi 5
            apt_type = apt.get("type", "Standard")
            print(f"  - {apt.get('task_id')} ({apt_type}) - {apt.get('address', 'N/A')}")
        if len(unassigned_final) > 5:
            print(f"  ... e altri {len(unassigned_final) - 5}")

    return assignments

def main(selected_date=None):
    """Funzione principale"""
    print("🔄 INIZIO ALGORITMO ASSEGNAZIONE")

    # Se viene passata una data come parametro da linea di comando
    if len(sys.argv) > 1:
        selected_date = sys.argv[1]

    print(f"📅 Data selezionata: {selected_date}")

    try:
        # Carica i cleaners selezionati
        sel_cleaners_data = load_json("data/sel_cleaners.json")

        # Usa la data specificata o cerca la data più recente
        if selected_date and "dates" in sel_cleaners_data and selected_date in sel_cleaners_data["dates"]:
            cleaners = sel_cleaners_data["dates"][selected_date].get("cleaners", [])
            print(f"✅ Usando cleaners dalla data specifica: {selected_date}")
        elif "dates" in sel_cleaners_data and sel_cleaners_data["dates"]:
            latest_date = max(sel_cleaners_data["dates"].keys())
            cleaners = sel_cleaners_data["dates"][latest_date].get("cleaners", [])
            print(f"⚠️ Usando cleaners dalla data più recente: {latest_date}")
        else:
            print("❌ Nessun cleaner trovato nel file sel_cleaners.json")
            return

        # Carica gli appartamenti
        apartments_data = load_json("data/modello_apt.json")

        # Usa la data specificata o cerca la data più recente per gli appartamenti
        if selected_date and "dates" in apartments_data and selected_date in apartments_data["dates"]:
            apartments = apartments_data["dates"][selected_date].get("apt", [])
            print(f"✅ Usando appartamenti dalla data specifica: {selected_date}")
        elif "dates" in apartments_data and apartments_data["dates"]:
            latest_date = max(apartments_data["dates"].keys())
            apartments = apartments_data["dates"][latest_date].get("apt", [])
            print(f"⚠️ Usando appartamenti dalla data più recente: {latest_date}")
        else:
            # Fallback al formato vecchio per compatibilità
            apartments = apartments_data.get("apt", [])
            print("⚠️ Usando appartamenti dal formato compatibilità (senza date)")

        #FILTRO APPARTAMENTI SENZA COORDINATE
        apartments = [apt for apt in apartments if apt.get("lat") and apt.get("lng")]

        if not cleaners:
            print("❌ Errore: Nessun cleaner selezionato trovato!")
            return

        if not apartments:
            print("❌ Errore: Nessun appartamento trovato!")
            return

        print(f"👥 Cleaners disponibili: {len(cleaners)}")
        print(f"🏠 Appartamenti da assegnare: {len(apartments)}")

        # Genera le assegnazioni
        assignments = build_assignments(cleaners, apartments)

        if not assignments:
            print("❌ Nessuna assegnazione generata!")
            return

        # Salva nel formato atteso dalle maschere
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "date": selected_date,
            "assignments": assignments,
            "total_cleaners": len(assignments),
            "total_apartments": sum(a["total_apartments"] for a in assignments)
        }

        with open("data/assignments.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Assegnazioni completate!")
        print(f"📊 Totale pacchetti: {len(assignments)}")
        print(f"🏠 Appartamenti assegnati: {sum(a['total_apartments'] for a in assignments)}")

        # Validazione appartamenti premium
        premium_apartments_assigned = 0
        premium_apartments_to_premium_cleaners = 0

        for assignment in assignments:
            for apt_detail in assignment["sequence_details"]:
                if apt_detail.get("type", "Standard").lower() == "premium":
                    premium_apartments_assigned += 1
                    if assignment["role"].lower() == "premium":
                        premium_apartments_to_premium_cleaners += 1

        total_premium_apts = len([apt for apt in apartments if apt.get("type", "Standard").lower() == "premium"])

        print(f"\n🏆 VALIDAZIONE APPARTAMENTI PREMIUM:")
        print(f"  📋 Totale apt premium: {total_premium_apts}")
        print(f"  ✅ Apt premium assegnati: {premium_apartments_assigned}")
        print(f"  🏆 Apt premium a cleaner premium: {premium_apartments_to_premium_cleaners}")

        if premium_apartments_to_premium_cleaners != premium_apartments_assigned:
            print(f"  ⚠️ ATTENZIONE: {premium_apartments_assigned - premium_apartments_to_premium_cleaners} apt premium assegnati a cleaner standard!")
        else:
            print(f"  ✅ Tutti gli appartamenti premium sono assegnati a cleaner premium!")

        # Stampa riepilogo
        for i, assignment in enumerate(assignments, 1):
            print(f"  {i}. {assignment['name']} {assignment['lastname']} ({assignment['role']}): {assignment['total_apartments']} apt")

    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()