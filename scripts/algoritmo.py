import json
import logging
import math
import numpy as np
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from gmaps import calcola_distanza


def setup_logging():
    """Configura il sistema di logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_cleaners():
    """Carica i cleaner selezionati dal file JSON"""
    try:
        with open('data/sel_cleaners.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            cleaners = data.get('cleaners', [])
            # Filtra solo i cleaner attivi e disponibili
            active_cleaners = [
                c for c in cleaners 
                if c.get('active', False) and c.get('available', False)
            ]
            logging.info(f"Caricati {len(active_cleaners)} cleaner attivi e disponibili su {len(cleaners)} totali")
            return active_cleaners
    except FileNotFoundError:
        logging.error("File data/sel_cleaners.json non trovato")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Errore nella lettura del file sel_cleaners.json: {e}")
        return []


def load_apartments():
    """Carica gli appartamenti dal file JSON"""
    try:
        with open('data/modello_apt.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            apartments = data.get('apt', [])
            # Filtra appartamenti con dati validi
            valid_apartments = []
            for apt in apartments:
                if apt.get('lat') and apt.get('lng') and apt.get('address'):
                    # Normalizza checkout_time se è None
                    if apt.get('checkout_time') is None:
                        apt['checkout_time'] = '15:00'
                    valid_apartments.append(apt)
                else:
                    logging.warning(f"Appartamento {apt.get('task_id')} ignorato per dati mancanti")

            logging.info(f"Caricati {len(valid_apartments)} appartamenti validi su {len(apartments)} totali")
            return valid_apartments
    except FileNotFoundError:
        logging.error("File data/modello_apt.json non trovato")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Errore nella lettura del file modello_apt.json: {e}")
        return []


def calculate_cleaning_time(apartment):
    """Calcola il tempo di pulizia per un appartamento in minuti"""
    # Se è specificato un cleaning_time, usalo
    if apartment.get('cleaning_time') is not None:
        return apartment['cleaning_time']

    # Altrimenti calcola in base ai parametri
    base_time = 90  # tempo base in minuti

    # Aggiungi tempo per pax_out (persone uscenti)
    pax_out = apartment.get('pax_out', 0)
    if pax_out > 2:
        base_time += (pax_out - 2) * 15

    # Riduci tempo per small_equipment
    if apartment.get('small_equipment', False):
        base_time = max(60, base_time - 20)

    # Tempo extra per appartamenti Premium
    if apartment.get('type') == 'Premium':
        base_time += 30

    return base_time


def create_cleaner_packages(apartments, cleaners):
    """Crea pacchetti di appartamenti per ogni cleaner"""
    logging.info("=== CREAZIONE PACCHETTI ===")

    # Separa appartamenti per tipo
    premium_apts = [apt for apt in apartments if apt.get('type') == 'Premium']
    standard_apts = [apt for apt in apartments if apt.get('type') == 'Standard']

    # Separa cleaner per ruolo
    premium_cleaners = [c for c in cleaners if c.get('role') == 'Premium']
    standard_cleaners = [c for c in cleaners if c.get('role') == 'Standard']

    logging.info(f"Appartamenti Premium: {len(premium_apts)}, Standard: {len(standard_apts)}")
    logging.info(f"Cleaner Premium: {len(premium_cleaners)}, Standard: {len(standard_cleaners)}")

    packages = {}

    # Assegna appartamenti Premium
    if premium_apts and premium_cleaners:
        packages['Premium'] = distribute_apartments_geographically(premium_apts, premium_cleaners)

    # Assegna appartamenti Standard
    if standard_apts and standard_cleaners:
        packages['Standard'] = distribute_apartments_geographically(standard_apts, standard_cleaners)

    return packages


def distribute_apartments_geographically(apartments, cleaners):
    """Distribuisce appartamenti geograficamente tra i cleaner"""
    n_cleaners = len(cleaners)
    if n_cleaners == 0:
        return []

    # Prepara coordinate per clustering
    coordinates = []
    apt_indices = []

    for i, apt in enumerate(apartments):
        try:
            lat = float(apt.get('lat', 0))
            lng = float(apt.get('lng', 0))
            if lat != 0 and lng != 0:
                coordinates.append([lat, lng])
                apt_indices.append(i)
        except (ValueError, TypeError):
            logging.warning(f"Coordinate non valide per appartamento {apt.get('task_id')}")

    if not coordinates:
        logging.error("Nessuna coordinata valida trovata")
        return []

    # Esegui clustering geografico
    n_clusters = min(n_cleaners, len(coordinates))
    if n_clusters > 1:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coordinates)
    else:
        labels = [0] * len(coordinates)

    # Crea clusters
    clusters = [[] for _ in range(n_clusters)]
    for apt_idx, cluster_label in zip(apt_indices, labels):
        clusters[cluster_label].append(apartments[apt_idx])

    # Bilancia i clusters (max 4 appartamenti per cleaner)
    balanced_clusters = balance_clusters(clusters, max_per_cluster=4)

    # Ordina ogni cluster per percorso ottimale
    optimized_packages = []
    for i, cluster in enumerate(balanced_clusters):
        if cluster:
            optimized_cluster = optimize_route_within_cluster(cluster)
            optimized_packages.append({
                'cleaner': cleaners[i] if i < len(cleaners) else cleaners[0],
                'apartments': optimized_cluster
            })

    return optimized_packages


def balance_clusters(clusters, max_per_cluster=4):
    """Bilancia i cluster per evitare sovraccarico"""
    balanced = []
    overflow = []

    # Prima passata: separa overflow
    for cluster in clusters:
        if len(cluster) <= max_per_cluster:
            balanced.append(cluster)
        else:
            balanced.append(cluster[:max_per_cluster])
            overflow.extend(cluster[max_per_cluster:])

    # Seconda passata: ridistribuisci overflow
    for apt in overflow:
        # Trova il cluster con meno appartamenti
        min_size = min(len(cluster) for cluster in balanced)
        if min_size < max_per_cluster:
            for cluster in balanced:
                if len(cluster) == min_size:
                    cluster.append(apt)
                    break
        else:
            # Se tutti sono pieni, crea nuovo cluster
            balanced.append([apt])

    return balanced


def optimize_route_within_cluster(apartments):
    """Ottimizza il percorso all'interno di un cluster"""
    if len(apartments) <= 1:
        return apartments

    # Ordina per orario di checkout, poi per small_equipment
    def sort_key(apt):
        checkout_time = apt.get('checkout_time')
        # Se checkout_time è None, imposta a 15:00
        if checkout_time is None:
            checkout_time = '15:00'
        has_small_equipment = apt.get('small_equipment', False)
        return (checkout_time, not has_small_equipment)  # small_equipment prima

    sorted_apts = sorted(apartments, key=sort_key)

    # Ulteriore ottimizzazione geografica se necessario
    if len(sorted_apts) > 2:
        return optimize_geographical_route(sorted_apts)

    return sorted_apts


def optimize_geographical_route(apartments):
    """Ottimizza geograficamente il percorso tra appartamenti"""
    if len(apartments) <= 2:
        return apartments

    # Algoritmo greedy per il percorso più breve
    route = [apartments[0]]  # Inizia dal primo
    remaining = apartments[1:]

    while remaining:
        current = route[-1]
        best_next = None
        best_distance = float('inf')

        for apt in remaining:
            try:
                lat1, lng1 = float(current.get('lat', 0)), float(current.get('lng', 0))
                lat2, lng2 = float(apt.get('lat', 0)), float(apt.get('lng', 0))

                # Calcola distanza semplificata (euclidea)
                distance = math.sqrt((lat2 - lat1)**2 + (lng2 - lng1)**2)

                if distance < best_distance:
                    best_distance = distance
                    best_next = apt
            except (ValueError, TypeError):
                continue

        if best_next:
            route.append(best_next)
            remaining.remove(best_next)
        else:
            # Se non riesce a calcolare distanze, prendi il prossimo
            route.append(remaining.pop(0))

    return route


def calculate_assignment_metrics(package):
    """Calcola le metriche per un'assegnazione"""
    apartments = package['apartments']
    if not apartments:
        return 0.0, 0.0

    total_cleaning_minutes = sum(calculate_cleaning_time(apt) for apt in apartments)
    total_travel_time = 0.0

    # Calcola tempo di viaggio tra appartamenti consecutivi
    for i in range(len(apartments) - 1):
        try:
            apt1, apt2 = apartments[i], apartments[i + 1]
            lat1, lng1 = float(apt1.get('lat', 0)), float(apt1.get('lng', 0))
            lat2, lng2 = float(apt2.get('lat', 0)), float(apt2.get('lng', 0))

            distance_result = calcola_distanza(lat1, lng1, lat2, lng2, mode='transit')
            if distance_result and 'durata' in distance_result:
                total_travel_time += distance_result['durata'] / 3600  # converti in ore
            else:
                # Fallback: stima basata su distanza euclidea
                distance_km = math.sqrt((lat2 - lat1)**2 + (lng2 - lng1)**2) * 111  # approssimazione
                total_travel_time += distance_km / 30  # 30 km/h media
        except (ValueError, TypeError) as e:
            logging.warning(f"Errore calcolo distanza: {e}")
            continue

    total_hours = (total_cleaning_minutes / 60.0) + total_travel_time
    return round(total_hours, 2), round(total_travel_time, 2)


def create_assignments(packages):
    """Crea le assegnazioni finali"""
    logging.info("=== CREAZIONE ASSEGNAZIONI ===")
    assignments = []

    for role, role_packages in packages.items():
        for package in role_packages:
            cleaner = package['cleaner']
            apartments = package['apartments']

            if not apartments:
                continue

            expected_hours, travel_hours = calculate_assignment_metrics(package)

            assignment = {
                'cleaner_id': cleaner['id'],
                'name': cleaner['name'],
                'lastname': cleaner['lastname'],
                'role': cleaner['role'],
                'expected_hours': expected_hours,
                'travel_hours': travel_hours,
                'apartments': [apt['task_id'] for apt in apartments],
                'apartment_details': apartments
            }

            assignments.append(assignment)

            logging.info(f"Assegnato a {cleaner['name']} {cleaner['lastname']}: {len(apartments)} appartamenti, {expected_hours}h totali")

    return assignments


def save_assignments(assignments):
    """Salva le assegnazioni su file nel formato corretto"""
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'assignments': assignments,
        'total_assignments': len(assignments)
    }

    with open('assignments.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logging.info(f"Assegnazioni salvate in assignments.json - {len(assignments)} assegnazioni totali")


def save_detailed_report(assignments, apartments):
    """Salva un report dettagliato"""
    apt_map = {apt['task_id']: apt for apt in apartments}

    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write("=== REPORT ASSEGNAZIONI ===\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Totale assegnazioni: {len(assignments)}\n\n")

        for i, assignment in enumerate(assignments, 1):
            f.write(f"{i}. CLEANER: {assignment['name']} {assignment['lastname']} ({assignment['role']})\n")
            f.write(f"   ID: {assignment['cleaner_id']}\n")
            f.write(f"   Ore previste: {assignment['expected_hours']}\n")
            f.write(f"   Appartamenti: {len(assignment['apartments'])}\n\n")

            for j, task_id in enumerate(assignment['apartments'], 1):
                apt = apt_map.get(task_id, {})
                f.write(f"   {j}. Task {task_id}\n")
                f.write(f"      Indirizzo: {apt.get('address', 'N/A')}\n")
                f.write(f"      Check-in: {apt.get('checkin', 'N/A')} {apt.get('checkin_time', '')}\n")
                f.write(f"      Check-out: {apt.get('checkout', 'N/A')} {apt.get('checkout_time', '')}\n")
                f.write(f"      Tempo pulizia: {calculate_cleaning_time(apt)} min\n")
                f.write(f"      Small equipment: {apt.get('small_equipment', False)}\n\n")

            f.write("-" * 50 + "\n\n")

    logging.info("Report dettagliato salvato in report.txt")


def main():
    """Funzione principale"""
    setup_logging()
    logging.info("=== INIZIO ALGORITMO ASSEGNAZIONE ===")

    # Carica dati freschi
    cleaners = load_cleaners()
    apartments = load_apartments()

    if not cleaners:
        logging.error("Nessun cleaner disponibile - interrompo esecuzione")
        return

    if not apartments:
        logging.error("Nessun appartamento disponibile - interrompo esecuzione")
        return

    # Debug info
    logging.info(f"Cleaner caricati: {len(cleaners)}")
    for cleaner in cleaners:
        logging.info(f"  - {cleaner['name']} {cleaner['lastname']} ({cleaner['role']}) - ID: {cleaner['id']}")

    logging.info(f"Appartamenti caricati: {len(apartments)}")

    # Crea pacchetti e assegnazioni
    packages = create_cleaner_packages(apartments, cleaners)
    assignments = create_assignments(packages)

    if not assignments:
        logging.error("Nessuna assegnazione creata")
        return

    # Salva risultati
    save_assignments(assignments)
    save_detailed_report(assignments, apartments)

    logging.info("=== ALGORITMO COMPLETATO CON SUCCESSO ===")
    logging.info(f"Totale assegnazioni create: {len(assignments)}")


if __name__ == '__main__':
    main()