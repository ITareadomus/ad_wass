import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from gmaps import calcola_distanza

from route_optimizer import optimize_route


# Configurazione logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Funzioni di refresh
def refresh_task_selection():
    try:
        logging.info('Eseguo task_selection.py per aggiornare la lista degli appartamenti...')
        subprocess.run(['python3', 'task_selection.py'], check=True)
        logging.info('Lista degli appartamenti aggiornata con successo.')
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore esecuzione task_selection.py: {e}")
        raise

def refresh_cleaner_selection():
    try:
        logging.info('Eseguo cleaner_selection.py per aggiornare la lista dei cleaner selezionati...')
        subprocess.run(['python3', 'cleaner_selection.py'], check=True)
        logging.info('Lista dei cleaner selezionati aggiornata con successo.')
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore esecuzione cleaner_selection.py: {e}")
        raise

# Caricamento dati dai JSON di input
def load_selected_cleaners():
    with open('sel_cleaners.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('cleaners', [])

def load_apartments():
    with open('mock_apartments.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('apt', [])

# FASE 1: Creazione pacchetti bilanciati (multi-processor scheduling)
'''def phase1_create_packages(apartments, cleaners):
    logging.info('--- FASE 1: Creazione pacchetti ---')

    def parse_datetime(date_str, time_str):
        try:
            return datetime.fromisoformat(f"{date_str}T{time_str}")
        except Exception:
            return None

    sorted_apts = sorted(
        apartments,
        key=lambda a: (a.get('checkout') or '', a.get('checkout_time') or '00:00')
    )

    # Conta i cleaner disponibili per ruolo
    role_cleaner_count = {}
    for c in cleaners:
        if c.get('active') and c.get('available'):
            role = c.get('role')
            role_cleaner_count[role] = role_cleaner_count.get(role, 0) + 1

    packets = {}
    for role, n_cleaners in role_cleaner_count.items():
        packets[role] = {'pkgs': [[] for _ in range(n_cleaners)], 'checkin_times': [[] for _ in range(n_cleaners)]}

    # Assegna gli appartamenti ai pacchetti in round-robin, rispettando i vincoli temporali
    for role in packets:
        pkgs = packets[role]['pkgs']
        checkin_times = packets[role]['checkin_times']
        role_apts = [a for a in sorted_apts if a.get('type') == role]
        n = len(pkgs)
        for idx, apt in enumerate(role_apts):
            cleaning_minutes = apt.get('cleaning_time') or 120
            ct_sec = cleaning_minutes * 60
            placed = False
            # Prova ad assegnare l'appartamento al prossimo pacchetto disponibile
            for offset in range(n):
                i = (idx + offset) % n
                pkg = pkgs[i]
                # Se il pacchetto è vuoto, si parte dal checkout
                if not pkg:
                    start_time = parse_datetime(apt.get('checkout'), apt.get('checkout_time') or '00:00')
                    finish_time = start_time + timedelta(seconds=ct_sec) if start_time else None
                    checkin_time = parse_datetime(apt.get('checkin'), apt.get('checkin_time') or '23:59')
                    if finish_time and checkin_time and finish_time <= checkin_time:
                        pkg.append(apt)
                        checkin_times[i].append(checkin_time)
                        placed = True
                        break
                    continue
                # Altrimenti, calcola il tempo di fine dell'ultimo apt
                last_apt = pkg[-1]
                last_finish = parse_datetime(last_apt.get('checkout'), last_apt.get('checkout_time') or '00:00')
                last_cleaning = last_apt.get('cleaning_time') or 120
                last_finish = last_finish + timedelta(minutes=last_cleaning) if last_finish else None
                try:
                    lat1 = float(last_apt.get('lat', 0))
                    lng1 = float(last_apt.get('lng', 0))
                    lat2 = float(apt.get('lat', 0))
                    lng2 = float(apt.get('lng', 0))
                except (TypeError, ValueError):
                    continue
                d = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
                travel_sec = d['durata'] if d else 0
                start_time = last_finish + timedelta(seconds=travel_sec) if last_finish else None
                finish_time = start_time + timedelta(seconds=ct_sec) if start_time else None
                checkin_time = parse_datetime(apt.get('checkin'), apt.get('checkin_time') or '23:59')
                if finish_time and checkin_time and finish_time <= checkin_time:
                    pkg.append(apt)
                    checkin_times[i].append(checkin_time)
                    placed = True
                    break
            if not placed:
                logging.warning(f"[TASK {apt.get('task_id')}] Non è stato possibile assegnare l'appartamento rispettando i vincoli temporali.")

    # Rimuovi eventuali pacchetti vuoti (non dovrebbero essercene)
    for role, data in packets.items():
        data['pkgs'] = [pkg for pkg in data['pkgs'] if pkg]
        data['checkin_times'] = [times for times in data['checkin_times'] if times]

    for role, data in packets.items():
        for i, pkg in enumerate(data['pkgs'], 1):
            logging.info(f"📦 Pacchetto {i}/{len(data['pkgs'])} '{role}' → {len(pkg)} apt")
    return {role: data['pkgs'] for role, data in packets.items()}'''

def phase1_create_packages(apartments, cleaners):
    logging.info('--- FASE 1: Creazione pacchetti ---')
    sorted_apts = sort_apartments_by_checkout(apartments)
    role_cleaner_count = count_cleaners_per_role(cleaners)
    packets = initialize_empty_packages(role_cleaner_count)
    packets = assign_apartments_to_packages(sorted_apts, packets)
    log_package_summary(packets)
    return {role: data['pkgs'] for role, data in packets.items()}


def sort_apartments_by_checkout(apartments):
    return sorted(
        apartments,
        key=lambda a: (a.get('checkout') or '', a.get('checkout_time') or '00:00')
    )

def count_cleaners_per_role(cleaners):
    role_cleaner_count = {}
    for c in cleaners:
        if c.get('active') and c.get('available'):
            role = c.get('role')
            role_cleaner_count[role] = role_cleaner_count.get(role, 0) + 1
    return role_cleaner_count

def initialize_empty_packages(role_cleaner_count):
    packets = {}
    for role, n_cleaners in role_cleaner_count.items():
        packets[role] = {
            'pkgs': [[] for _ in range(n_cleaners)],
            'checkin_times': [[] for _ in range(n_cleaners)]
        }
    return packets


def parse_datetime(date_str, time_str):
    try:
        return datetime.fromisoformat(f"{date_str}T{time_str}")
    except Exception:
        return None


def assign_apartments_to_packages(sorted_apts, packets):
    for role in packets:
        pkgs = packets[role]['pkgs']
        checkin_times = packets[role]['checkin_times']
        role_apts = [a for a in sorted_apts if a.get('type') == role]
        n = len(pkgs)
        for idx, apt in enumerate(role_apts):
            cleaning_minutes = apt.get('cleaning_time') or 120
            ct_sec = cleaning_minutes * 60
            placed = False
            for offset in range(n):
                i = (idx + offset) % n
                pkg = pkgs[i]
                if not pkg:
                    start_time = parse_datetime(apt.get('checkout'), apt.get('checkout_time') or '00:00')
                    finish_time = start_time + timedelta(seconds=ct_sec) if start_time else None
                    checkin_time = parse_datetime(apt.get('checkin'), apt.get('checkin_time') or '23:59')
                    if finish_time and checkin_time and finish_time <= checkin_time:
                        pkg.append(apt)
                        checkin_times[i].append(checkin_time)
                        placed = True
                        break
                    continue
                last_apt = pkg[-1]
                last_finish = parse_datetime(last_apt.get('checkout'), last_apt.get('checkout_time') or '00:00')
                last_cleaning = last_apt.get('cleaning_time') or 120
                last_finish = last_finish + timedelta(minutes=last_cleaning) if last_finish else None
                try:
                    lat1, lng1 = float(last_apt.get('lat', 0)), float(last_apt.get('lng', 0))
                    lat2, lng2 = float(apt.get('lat', 0)), float(apt.get('lng', 0))
                except (TypeError, ValueError):
                    continue
                d = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
                travel_sec = d['durata'] if d else 0
                start_time = last_finish + timedelta(seconds=travel_sec) if last_finish else None
                finish_time = start_time + timedelta(seconds=ct_sec) if start_time else None
                checkin_time = parse_datetime(apt.get('checkin'), apt.get('checkin_time') or '23:59')
                if finish_time and checkin_time and finish_time <= checkin_time:
                    pkg.append(apt)
                    checkin_times[i].append(checkin_time)
                    placed = True
                    break
            if not placed:
                logging.warning(f"[TASK {apt.get('task_id')}] Non è stato possibile assegnare l'appartamento rispettando i vincoli temporali.")

    # Rimuove pacchetti vuoti
    for role, data in packets.items():
        data['pkgs'] = [pkg for pkg in data['pkgs'] if pkg]
        data['checkin_times'] = [times for times in data['checkin_times'] if times]

    # ⬅️ Sposta questo blocco prima del return
    for role, data in packets.items():
        data['pkgs'] = [reorder_package_by_distance(pkg) for pkg in data['pkgs']]

    return packets

def reorder_package_by_distance(pkg):
    if not pkg:
        return pkg

    ordered = [pkg[0]]
    remaining = pkg[1:]

    while remaining:
        last = ordered[-1]
        try:
            lat1, lng1 = float(last.get('lat', 0)), float(last.get('lng', 0))
        except (TypeError, ValueError):
            logging.warning("Coordinate non valide nel pacchetto.")
            break

        try:
            next_apt = min(
                remaining,
                key=lambda apt: calcola_distanza(
                    lat1, lng1,
                    float(apt.get('lat', 0)), float(apt.get('lng', 0)),
                    mode='walking'
                ).get('durata', float('inf'))  # <-- ora usa durata
            )
        except Exception as e:
            logging.warning(f"Errore durante il riordino per distanza: {e}")
            break

        ordered.append(next_apt)
        remaining.remove(next_apt)

    return ordered


def log_package_summary(packets):
    for role, data in packets.items():
        for i, pkg in enumerate(data['pkgs'], 1):
            logging.info(f"📦 Pacchetto {i}/{len(data['pkgs'])} '{role}' → {len(pkg)} apt")

# FASE 2: Ordinamento all'interno dei pacchetti
def phase2_order_packages(packages):
    logging.info('--- FASE 2: Ordinamento interno pacchetti ---')
    def priority(a):
        return (0,a.get('checkin_time') or '23:59') if a.get('small_equipment') else (1,a.get('checkin_time') or '23:59')
    ordered={}
    for role,pkgs in packages.items():
        ordered[role]=[sorted(pkg,key=priority) for pkg in pkgs]
        for i,pkg in enumerate(ordered[role],1):
            logging.info(f"Pacchetto {i}/{len(pkgs)} '{role}' ordinato: {[a['task_id'] for a in pkg]}")
    return ordered

# FASE 3: Assegnazione e calcolo expected_hours (cleaning_time -> ore)
def phase3_assign_to_cleaners(ordered, cleaners):
    logging.info('--- FASE 3: Assegnazione pacchetti ai cleaner ---')
    assignments = []

    # Mappa cleaner per ruolo, con ore assegnate
    cleaner_map = {
        role: [
            {
                'id': c['id'],
                'name': c['name'],
                'lastname': c['lastname'],
                'role': c['role'],
                'ranking': c.get('ranking', 0),
                'counter_hours': c.get('counter_hours', 0.0),
                'assigned_hours': 0.0,
                'apartments': []
            }
            for c in cleaners if c.get('role') == role and c.get('active') and c.get('available')
        ]
        for role in ordered.keys()
    }

    for role, pkgs in ordered.items():
        for pkg in pkgs:
            total_clean = sum(a.get('cleaning_time') if a.get('cleaning_time') is not None else 120 for a in pkg)
            total_travel = 0
            for i in range(len(pkg) - 1):
                try:
                    lat1 = float(pkg[i].get('lat', 0))
                    lng1 = float(pkg[i].get('lng', 0))
                    lat2 = float(pkg[i+1].get('lat', 0))
                    lng2 = float(pkg[i+1].get('lng', 0))
                except (TypeError, ValueError):
                    continue
                d = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
                if d:
                    total_travel += d['distanza_metri'] / 1.4 / 3600

            expected_hours = round((total_clean / 60.0) + total_travel, 2)

            # Nessun cleaner disponibile per questo ruolo
            if not cleaner_map[role]:
                logging.warning(f"Nessun cleaner disponibile per il ruolo '{role}' – pacchetto non assegnato.")
                continue

            # Assegna al cleaner con meno ore totali (assegnate + counter_hours), poi ranking
            cands = sorted(
                cleaner_map[role],
                key=lambda c: (c['assigned_hours'] + c['counter_hours'], -c['ranking'])
            )
            chosen = cands[0]
            chosen['assigned_hours'] += expected_hours
            chosen['apartments'].extend([a['task_id'] for a in pkg])

            logging.info(f"Assegnato {[a['task_id'] for a in pkg]} a {chosen['name']} {chosen['lastname']} ({expected_hours}h)")
            for role, data in packets.items():
                for i, pkg in enumerate(data['pkgs']):
                    logging.info(f"[{role} - pacchetto {i}] Task IDs: {[apt['task_id'] for apt in pkg]}")
    # Ritorna solo cleaner con appartamenti assegnati
    for clist in cleaner_map.values():
        for c in clist:
            if c['apartments']:
                assignments.append({
                    'cleaner_id': c['id'],
                    'name': c['name'],
                    'lastname': c['lastname'],
                    'role': c['role'],
                    'expected_hours': round(c['assigned_hours'], 2),
                    'apartments': c['apartments']
                })

    return assignments


# Genera un report dettagliato in testo
def save_detailed_report(assignments, apartments):
    map_apt = {a['task_id']: a for a in apartments}
    with open('report.txt', 'w', encoding='utf-8') as f:
        for asg in assignments:
            f.write(f"Cleaner: {asg['name']} {asg['lastname']} ({asg['role']})\n")
            seq = asg['apartments']
            for idx, tid in enumerate(seq):
                apt = map_apt.get(tid, {})
                f.write(f"  {idx+1}. Task {tid}: {apt.get('address','')} - checkin: {apt.get('checkin','')} {apt.get('checkin_time','')} | checkout: {apt.get('checkout','')} {apt.get('checkout_time','')}\n")
                if idx+1 < len(seq):
                    next_apt = map_apt.get(seq[idx+1], {})
                    try:
                        lat1 = float(apt.get('lat', 0))
                        lng1 = float(apt.get('lng', 0))
                        lat2 = float(next_apt.get('lat', 0))
                        lng2 = float(next_apt.get('lng', 0))
                    except (TypeError, ValueError):
                        continue
                    d = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
                    if d:
                        durata_min = round(d['durata'] / 60, 1)
                        f.write(f"     -> distanza: {d['distanza_metri']}m, durata: {durata_min} min\n")
            # AGGIUNTA: riepilogo ore totali
            f.write(f"\n  ➤ Totale ore assegnate: {asg.get('expected_hours', 0)}\n\n")
    logging.info("Report dettagliato salvato in 'report.txt'.")
# Salvataggio JSON e report
def save_assignments(assignments):
    with open('assignments.json','w',encoding='utf-8') as f:
        json.dump({'assignment':assignments},f,indent=4,ensure_ascii=False)
    logging.info("Assegnazioni salvate in 'assignments.json'.")

# Main
def main():
    setup_logging()
    logging.info('Inizio algoritmo di assegnazione')
    #refresh_task_selection()
    refresh_cleaner_selection()

    cleaners = load_selected_cleaners()
    apartments = load_apartments()

    # 🔍 DEBUG: controllo cleaner disponibili
    active_available = [c for c in cleaners if c.get('active') and c.get('available')]
    logging.info(f"[DEBUG] Cleaner totali: {len(cleaners)}")
    logging.info(f"[DEBUG] Cleaner disponibili (active=True AND available=True): {len(active_available)}")
    for c in active_available:
        logging.info(f"[DEBUG] ✓ Cleaner ID: {c.get('id')} | Nome: {c.get('name')} {c.get('lastname')} | Ruolo: {c.get('role')} | Ranking: {c.get('ranking')}")

    packages = phase1_create_packages(apartments, cleaners)
    ordered = phase2_order_packages(packages)
    assignments = phase3_assign_to_cleaners(ordered, cleaners)
    save_assignments(assignments)
    save_detailed_report(assignments, apartments)
    logging.info('Esecuzione completata con successo.')

    print("Python path:", sys.executable)
    print("Python version:", sys.version)


if __name__=='__main__':
    main()