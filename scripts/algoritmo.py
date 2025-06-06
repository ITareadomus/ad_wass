
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from gmaps import calcola_distanza

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
        subprocess.run(['python3', 'scripts/task_selection.py'], check=True)
        logging.info('Lista degli appartamenti aggiornata con successo.')
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore esecuzione task_selection.py: {e}")
        raise

def refresh_cleaner_selection():
    try:
        logging.info('Eseguo cleaner_selection.py per aggiornare la lista dei cleaner selezionati...')
        subprocess.run(['python3', 'scripts/cleaner_selection.py'], check=True)
        logging.info('Lista dei cleaner selezionati aggiornata con successo.')
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore esecuzione cleaner_selection.py: {e}")
        raise

# Caricamento dati dai JSON di input
def load_selected_cleaners():
    with open('data/sel_cleaners.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('cleaners', [])

def load_apartments():
    with open('data/modello_apt.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('apt', [])

# Funzione per determinare se un appartamento ha priorità 1
def is_priority_1(apt):
    """
    Un appartamento ha priorità 1 se:
    - Ha check-in alle 14:00 OR
    - Ha small_equipment = true
    """
    checkin_time = apt.get('checkin_time', '')
    small_equipment = apt.get('small_equipment', False)
    return checkin_time == '14:00' or small_equipment

# Funzione per trovare appartamenti vicini nel raggio di 800m
def find_nearby_apartments(target_apt, available_apts, radius_meters=800):
    """
    Trova tutti gli appartamenti disponibili nel raggio specificato dal target_apt
    """
    nearby = []
    try:
        target_lat = float(target_apt.get('lat', 0))
        target_lng = float(target_apt.get('lng', 0))
    except (TypeError, ValueError):
        return nearby
    
    for apt in available_apts:
        if apt['task_id'] == target_apt['task_id']:
            continue
        try:
            apt_lat = float(apt.get('lat', 0))
            apt_lng = float(apt.get('lng', 0))
        except (TypeError, ValueError):
            continue
        
        distance_info = calcola_distanza(target_lat, target_lng, apt_lat, apt_lng, mode='walking')
        if distance_info and distance_info['distanza_metri'] <= radius_meters:
            nearby.append((apt, distance_info['distanza_metri']))
    
    # Ordina per distanza crescente
    nearby.sort(key=lambda x: x[1])
    return [apt for apt, _ in nearby]

# Funzione per trovare l'appartamento più vicino
def find_closest_apartment(target_apt, available_apts):
    """
    Trova l'appartamento più vicino tra quelli disponibili
    """
    if not available_apts:
        return None
    
    try:
        target_lat = float(target_apt.get('lat', 0))
        target_lng = float(target_apt.get('lng', 0))
    except (TypeError, ValueError):
        return available_apts[0] if available_apts else None
    
    closest = None
    min_distance = float('inf')
    
    for apt in available_apts:
        if apt['task_id'] == target_apt['task_id']:
            continue
        try:
            apt_lat = float(apt.get('lat', 0))
            apt_lng = float(apt.get('lng', 0))
        except (TypeError, ValueError):
            continue
        
        distance_info = calcola_distanza(target_lat, target_lng, apt_lat, apt_lng, mode='walking')
        if distance_info and distance_info['distanza_metri'] < min_distance:
            min_distance = distance_info['distanza_metri']
            closest = apt
    
    return closest

# FASE 1: Creazione sequenze di appartamenti
def phase1_create_sequences(apartments):
    logging.info('--- FASE 1: Creazione sequenze di appartamenti ---')
    
    # Separa appartamenti per tipo
    premium_apts = [apt for apt in apartments if apt.get('type') == 'Premium']
    standard_apts = [apt for apt in apartments if apt.get('type') == 'Standard']
    
    # Crea sequenze per ogni tipo
    premium_sequences = create_sequences_for_type(premium_apts, 'Premium')
    standard_sequences = create_sequences_for_type(standard_apts, 'Standard')
    
    return {
        'Premium': premium_sequences,
        'Standard': standard_sequences
    }

def create_sequences_for_type(apartments, apt_type):
    """
    Crea sequenze di appartamenti seguendo la logica di priorità e distanza
    """
    sequences = []
    available = apartments.copy()
    
    logging.info(f"Creazione sequenze per tipo {apt_type}: {len(available)} appartamenti disponibili")
    
    while available:
        sequence = create_single_sequence(available)
        if sequence:
            sequences.append(sequence)
            # Rimuovi gli appartamenti utilizzati dalla lista disponibili
            for apt in sequence:
                if apt in available:
                    available.remove(apt)
        else:
            # Se non riusciamo a creare una sequenza, prendiamo il primo disponibile
            if available:
                sequences.append([available.pop(0)])
    
    logging.info(f"Create {len(sequences)} sequenze per {apt_type}")
    return sequences

def create_single_sequence(available_apts):
    """
    Crea una singola sequenza di 3 appartamenti seguendo la logica specificata
    """
    if not available_apts:
        return []
    
    sequence = []
    remaining = available_apts.copy()
    
    # 1. Trova un appartamento di priorità 1 come punto di partenza
    priority_1_apts = [apt for apt in remaining if is_priority_1(apt)]
    
    if priority_1_apts:
        # Inizia con un appartamento di priorità 1
        current_apt = priority_1_apts[0]
    else:
        # Se non ci sono appartamenti di priorità 1, prendi il primo disponibile
        current_apt = remaining[0]
    
    sequence.append(current_apt)
    remaining.remove(current_apt)
    
    # 2. Aggiungi fino a 2 altri appartamenti (max 3 per sequenza)
    while len(sequence) < 3 and remaining:
        next_apt = find_next_apartment(current_apt, remaining)
        if next_apt:
            sequence.append(next_apt)
            remaining.remove(next_apt)
            current_apt = next_apt
        else:
            break
    
    return sequence

def find_next_apartment(current_apt, available_apts):
    """
    Trova il prossimo appartamento da aggiungere alla sequenza
    Logica: priorità 1 nel raggio di 800m, altrimenti il più vicino
    """
    if not available_apts:
        return None
    
    # 1. Cerca appartamenti di priorità 1 nel raggio di 800m
    nearby_apts = find_nearby_apartments(current_apt, available_apts, 800)
    priority_1_nearby = [apt for apt in nearby_apts if is_priority_1(apt)]
    
    if priority_1_nearby:
        return priority_1_nearby[0]  # Prendi il primo (più vicino) di priorità 1
    
    # 2. Se non ci sono priorità 1 nel raggio, cerca qualsiasi appartamento nel raggio
    if nearby_apts:
        return nearby_apts[0]  # Prendi il più vicino nel raggio
    
    # 3. Se nessuno è nel raggio di 800m, prendi il più vicino in assoluto
    return find_closest_apartment(current_apt, available_apts)

# FASE 2: Assegnazione sequenze ai cleaner
def phase2_assign_sequences_to_cleaners(sequences, cleaners):
    logging.info('--- FASE 2: Assegnazione sequenze ai cleaner ---')
    
    assignments = []
    
    # Prepara i cleaner per ruolo
    cleaner_map = {
        'Premium': [c for c in cleaners if c.get('role') == 'Premium' and c.get('active') and c.get('available')],
        'Standard': [c for c in cleaners if c.get('role') == 'Standard' and c.get('active') and c.get('available')]
    }
    
    # Inizializza il contatore delle ore assegnate per ogni cleaner
    for role_cleaners in cleaner_map.values():
        for cleaner in role_cleaners:
            cleaner['assigned_hours'] = 0.0
    
    # Assegna sequenze per ogni tipo
    for apt_type, type_sequences in sequences.items():
        available_cleaners = cleaner_map.get(apt_type, [])
        
        if not available_cleaners:
            logging.warning(f"Nessun cleaner disponibile per il tipo {apt_type}")
            continue
        
        for sequence in type_sequences:
            if not sequence:
                continue
            
            # Calcola le ore totali per questa sequenza
            total_hours = calculate_sequence_hours(sequence)
            
            # Trova il cleaner con meno ore totali (assegnate + counter_hours)
            best_cleaner = min(
                available_cleaners,
                key=lambda c: (c['assigned_hours'] + c.get('counter_hours', 0), -c.get('ranking', 0))
            )
            
            # Assegna la sequenza al cleaner
            best_cleaner['assigned_hours'] += total_hours
            
            assignment = {
                'cleaner_id': best_cleaner.get('id'),
                'name': best_cleaner.get('name'),
                'lastname': best_cleaner.get('lastname'),
                'role': best_cleaner.get('role'),
                'expected_hours': round(total_hours, 2),
                'apartments': [apt['task_id'] for apt in sequence],
                'sequence_details': [
                    {
                        'task_id': apt['task_id'],
                        'address': apt.get('address', ''),
                        'lat': apt.get('lat'),
                        'lng': apt.get('lng'),
                        'checkin': apt.get('checkin'),
                        'checkin_time': apt.get('checkin_time'),
                        'checkout': apt.get('checkout'),
                        'checkout_time': apt.get('checkout_time'),
                        'cleaning_time': apt.get('cleaning_time', 120),
                        'small_equipment': apt.get('small_equipment', False),
                        'priority_1': is_priority_1(apt)
                    }
                    for apt in sequence
                ]
            }
            
            assignments.append(assignment)
            
            logging.info(f"Assegnata sequenza {[apt['task_id'] for apt in sequence]} a {best_cleaner['name']} {best_cleaner['lastname']} ({total_hours}h)")
    
    return assignments

def calculate_sequence_hours(sequence):
    """
    Calcola le ore totali per una sequenza di appartamenti
    Include tempo di pulizia + tempo di viaggio
    """
    if not sequence:
        return 0.0
    
    # Tempo di pulizia totale
    total_cleaning_minutes = sum(apt.get('cleaning_time', 120) for apt in sequence)
    
    # Tempo di viaggio tra appartamenti
    total_travel_hours = 0.0
    for i in range(len(sequence) - 1):
        current_apt = sequence[i]
        next_apt = sequence[i + 1]
        
        try:
            lat1 = float(current_apt.get('lat', 0))
            lng1 = float(current_apt.get('lng', 0))
            lat2 = float(next_apt.get('lat', 0))
            lng2 = float(next_apt.get('lng', 0))
            
            distance_info = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
            if distance_info:
                travel_hours = distance_info['durata'] / 3600  # converti secondi in ore
                total_travel_hours += travel_hours
        except (TypeError, ValueError):
            continue
    
    total_hours = (total_cleaning_minutes / 60.0) + total_travel_hours
    return total_hours

# Genera un report dettagliato
def save_detailed_report(assignments):
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write("=== REPORT ASSEGNAZIONI ===\n\n")
        
        for assignment in assignments:
            f.write(f"Cleaner: {assignment['name']} {assignment['lastname']} ({assignment['role']})\n")
            f.write(f"Ore totali assegnate: {assignment['expected_hours']}\n")
            f.write(f"Numero appartamenti: {len(assignment['apartments'])}\n\n")
            
            for i, detail in enumerate(assignment['sequence_details'], 1):
                priority_text = " [PRIORITÀ 1]" if detail['priority_1'] else ""
                equipment_text = " [SMALL EQUIPMENT]" if detail['small_equipment'] else ""
                
                f.write(f"  {i}. Task {detail['task_id']}{priority_text}{equipment_text}\n")
                f.write(f"     Indirizzo: {detail['address']}\n")
                f.write(f"     Check-in: {detail['checkin']} {detail['checkin_time']}\n")
                f.write(f"     Check-out: {detail['checkout']} {detail['checkout_time']}\n")
                f.write(f"     Tempo pulizia: {detail['cleaning_time']} min\n")
                
                # Calcola distanza al prossimo appartamento
                if i < len(assignment['sequence_details']):
                    next_detail = assignment['sequence_details'][i]
                    try:
                        lat1 = float(detail['lat'])
                        lng1 = float(detail['lng'])
                        lat2 = float(next_detail['lat'])
                        lng2 = float(next_detail['lng'])
                        
                        distance_info = calcola_distanza(lat1, lng1, lat2, lng2, mode='walking')
                        if distance_info:
                            f.write(f"     -> Distanza al prossimo: {distance_info['distanza_metri']}m ({distance_info['durata']//60} min)\n")
                    except (TypeError, ValueError, IndexError):
                        pass
                
                f.write("\n")
            
            f.write("-" * 50 + "\n\n")
    
    logging.info("Report dettagliato salvato in 'report.txt'")

# Salvataggio JSON
def save_assignments(assignments):
    with open('data/assignments.json', 'w', encoding='utf-8') as f:
        json.dump({'assignments': assignments}, f, indent=4, ensure_ascii=False)
    logging.info("Assegnazioni salvate in 'data/assignments.json'")

# Main
def main():
    setup_logging()
    logging.info('Inizio algoritmo di assegnazione con logica di priorità e distanza')
    
    # Carica i dati
    try:
        cleaners = load_selected_cleaners()
        apartments = load_apartments()
    except FileNotFoundError as e:
        logging.error(f"File non trovato: {e}")
        return
    
    # Debug info
    active_cleaners = [c for c in cleaners if c.get('active') and c.get('available')]
    priority_1_apts = [apt for apt in apartments if is_priority_1(apt)]
    
    logging.info(f"Appartamenti totali: {len(apartments)}")
    logging.info(f"Appartamenti priorità 1: {len(priority_1_apts)}")
    logging.info(f"Cleaner disponibili: {len(active_cleaners)}")
    
    # Esegui l'algoritmo
    sequences = phase1_create_sequences(apartments)
    assignments = phase2_assign_sequences_to_cleaners(sequences, cleaners)
    
    # Salva i risultati
    save_assignments(assignments)
    save_detailed_report(assignments)
    
    logging.info(f'Algoritmo completato: {len(assignments)} assegnazioni create')

if __name__ == '__main__':
    main()
