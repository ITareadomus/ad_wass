import json
import logging
import subprocess
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
        logging.info('Eseguo cleaner_selection.py per aggiornare la lista dei cleaner.')
        subprocess.run(['python3', 'cleaner_selection.py'], check=True)
        logging.info('Lista dei cleaner aggiornata con successo.')
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
def phase1_create_packages(apartments, cleaners, max_duration_hours=4, radius_m=3000):
    logging.info('--- FASE 1: Creazione pacchetti ---')
    def parse_date(dt):
        try:
            return datetime.fromisoformat(dt).date()
        except:
            return None

    def safe_date(dt):
        d = parse_date(dt)
        return d if d is not None else datetime.max.date()

    sorted_apts = sorted(
        apartments,
        key=lambda a: (safe_date(a.get('checkin')), a.get('checkin_time') or '23:59')
    )

    # Inizializza pacchetti e remaining per ogni ruolo
    packets = {}
    for c in cleaners:
        if c.get('active') and c.get('available'):
            role = c.get('role')
            packets.setdefault(role, {'pkgs': [], 'remaining': []})
    for role, data in packets.items():
        count = sum(1 for c in cleaners if c.get('role') == role and c.get('active') and c.get('available'))
        data['pkgs'] = [[] for _ in range(count)]
        data['remaining'] = [max_duration_hours*3600]*count

    # Distribuisci apartment
    for apt in sorted_apts:
        role = apt.get('type')
        if role not in packets: continue
        data = packets[role]
        cleaning_minutes = apt.get('cleaning_time')
        if cleaning_minutes is None:
            cleaning_minutes = 120  # default 2 ore
        ct_sec = cleaning_minutes * 60
        # ordina indici per remaining decrescente
        idxs = sorted(range(len(data['pkgs'])), key=lambda i: data['remaining'][i], reverse=True)
        placed = False
        for i in idxs:
            pkg = data['pkgs'][i]
            if not pkg:
                pkg.append(apt)
                data['remaining'][i] -= ct_sec
                placed = True
                break
            last = pkg[-1]
            try:
                last_lat = float(last.get('lat', 0))
                last_lng = float(last.get('lng', 0))
                apt_lat = float(apt.get('lat', 0))
                apt_lng = float(apt.get('lng', 0))
            except (TypeError, ValueError):
                continue
            d = calcola_distanza(last_lat, last_lng, apt_lat, apt_lng, mode='walking')
            if d:
                travel = d['distanza_metri']/1.4
                if d['distanza_metri'] <= radius_m and ct_sec+travel <= data['remaining'][i]:
                    pkg.append(apt)
                    data['remaining'][i] -= (ct_sec+travel)
                    placed = True
                    break
        if not placed:
            i = idxs[0]
            packets[role]['pkgs'][i].append(apt)
            packets[role]['remaining'][i] -= ct_sec

    for role, data in packets.items():
        for i, pkg in enumerate(data['pkgs'], 1):
            logging.info(f"Pacchetto {i}/{len(data['pkgs'])} '{role}' con {len(pkg)} apt (remaining {data['remaining'][i-1]}s)")
    return {role: data['pkgs'] for role, data in packets.items()}

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
    for role, pkgs in ordered.items():
        cands = sorted([c for c in cleaners if c.get('role') == role and c.get('active') and c.get('available')],
                       key=lambda c: (-c.get('ranking', 0), c.get('counter_hours', 0)))
        for cleaner, pkg in zip(cands, pkgs):
            total_clean = sum(a.get('cleaning_time') if a.get('cleaning_time') is not None else 120 for a in pkg)
            total_travel = 0
            for i in range(len(pkg)-1):
                try:
                    lat1 = float(pkg[i].get('lat', 0))
                    lng1 = float(pkg[i].get('lng', 0))
                    lat2 = float(pkg[i+1].get('lat', 0))
                    lng2 = float(pkg[i+1].get('lng', 0))
                except (TypeError, ValueError):
                    continue
                d = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
                if d:
                    total_travel += d['distanza_metri']/1.4/3600
            expected = round((total_clean/60.0) + total_travel, 2)
            assignments.append({
                'cleaner_id': cleaner['id'],
                'name': cleaner['name'],
                'lastname': cleaner['lastname'],
                'role': role,
                'expected_hours': expected,
                'apartments': [a['task_id'] for a in pkg]
            })
            logging.info(f"Assegnato {[a['task_id'] for a in pkg]} a {cleaner['name']} {cleaner['lastname']} ({expected}h)")
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
                        f.write(f"     -> distanza: {d['distanza_metri']}m, durata: {d['durata']}\n")
            f.write("\n")
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
    refresh_task_selection(); refresh_cleaner_selection()
    cleaners=load_selected_cleaners(); apartments=load_apartments()
    packages=phase1_create_packages(apartments,cleaners)
    ordered=phase2_order_packages(packages)
    assignments=phase3_assign_to_cleaners(ordered,cleaners)
    save_assignments(assignments)
    save_detailed_report(assignments,apartments)
    logging.info('Esecuzione completata con successo.')

if __name__=='__main__':
    main()