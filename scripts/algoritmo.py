import json
import logging
import random
from datetime import datetime


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
            # Filtra appartamenti con dati validi (almeno task_id e address)
            valid_apartments = []
            for apt in apartments:
                if apt.get('task_id') and apt.get('address'):
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


def assign_random_apartments(cleaners, apartments):
    """Assegna casualmente 3 appartamenti a ogni cleaner"""
    logging.info("=== ASSEGNAZIONE CASUALE APPARTAMENTI ===")

    assignments = []
    available_apartments = apartments.copy()

    # Mescola gli appartamenti per renderli casuali
    random.shuffle(available_apartments)

    for cleaner in cleaners:
        # Prendi fino a 3 appartamenti per questo cleaner
        assigned_apartments = []
        apartments_to_assign = min(3, len(available_apartments))

        for _ in range(apartments_to_assign):
            if available_apartments:
                apartment = available_apartments.pop(0)

                # Aggiungi priorità casuale
                apartment['priority_1'] = random.choice([True, False])

                assigned_apartments.append(apartment)

        if assigned_apartments:
            # Calcola ore stimate casuali (tra 2 e 6 ore)
            expected_hours = round(random.uniform(2.0, 6.0), 2)
            travel_hours = round(random.uniform(0.1, 0.5), 2)

            assignment = {
                'cleaner_id': cleaner['id'],
                'name': cleaner['name'],
                'lastname': cleaner['lastname'],
                'role': cleaner['role'],
                'expected_hours': expected_hours,
                'travel_hours': travel_hours,
                'apartments': [apt['task_id'] for apt in assigned_apartments],
                'apartment_details': assigned_apartments
            }

            assignments.append(assignment)

            logging.info(f"Assegnato a {cleaner['name']} {cleaner['lastname']}: {len(assigned_apartments)} appartamenti")

    # Se rimangono appartamenti non assegnati, distribuiscili
    if available_apartments:
        logging.info(f"Rimangono {len(available_apartments)} appartamenti non assegnati")
        redistribute_remaining_apartments(assignments, available_apartments)

    return assignments


def redistribute_remaining_apartments(assignments, remaining_apartments):
    """Ridistribuisce gli appartamenti rimanenti tra i cleaner esistenti"""
    if not assignments or not remaining_apartments:
        return

    logging.info(f"Ridistribuzione di {len(remaining_apartments)} appartamenti rimanenti")

    for apartment in remaining_apartments:
        # Scegli un cleaner casuale per questo appartamento
        assignment = random.choice(assignments)

        # Aggiungi priorità casuale
        apartment['priority_1'] = random.choice([True, False])

        # Aggiungi l'appartamento all'assegnazione
        assignment['apartments'].append(apartment['task_id'])
        assignment['apartment_details'].append(apartment)

        # Aggiorna le ore stimate (aggiungi 1-2 ore)
        assignment['expected_hours'] += round(random.uniform(1.0, 2.0), 2)
        assignment['travel_hours'] += round(random.uniform(0.05, 0.15), 2)

        logging.info(f"Appartamento {apartment['task_id']} ridistribuito a {assignment['name']} {assignment['lastname']}")


def save_assignments(assignments):
    """Salva le assegnazioni su file nel formato corretto"""
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'assignments': assignments,
        'total_assignments': len(assignments)
    }

    with open('data/assignments.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logging.info(f"Assegnazioni salvate in data/assignments.json - {len(assignments)} assegnazioni totali")


def save_detailed_report(assignments):
    """Salva un report dettagliato"""
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write("=== REPORT ASSEGNAZIONI CASUALI ===\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Totale assegnazioni: {len(assignments)}\n\n")

        for i, assignment in enumerate(assignments, 1):
            f.write(f"{i}. CLEANER: {assignment['name']} {assignment['lastname']} ({assignment['role']})\n")
            f.write(f"   ID: {assignment['cleaner_id']}\n")
            f.write(f"   Ore previste: {assignment['expected_hours']}\n")
            f.write(f"   Ore viaggio: {assignment['travel_hours']}\n")
            f.write(f"   Appartamenti: {len(assignment['apartments'])}\n\n")

            for j, apartment in enumerate(assignment['apartment_details'], 1):
                priority_text = " [PRIORITÀ]" if apartment.get('priority_1', False) else ""
                f.write(f"   {j}. Task {apartment['task_id']}{priority_text}\n")
                f.write(f"      Indirizzo: {apartment.get('address', 'N/A')}\n")
                f.write(f"      Check-out: {apartment.get('checkout', 'N/A')} {apartment['checkout_time']}\n")
                f.write(f"      Tipo: {apartment.get('type', 'Standard')}\n")
                f.write(f"      Small equipment: {apartment.get('small_equipment', False)}\n\n")

            f.write("-" * 50 + "\n\n")

    logging.info("Report dettagliato salvato in report.txt")


def main():
    """Funzione principale"""
    setup_logging()
    logging.info("=== INIZIO ALGORITMO ASSEGNAZIONE CASUALE ===")

    # Imposta il seed per la casualità (opzionale, per risultati riproducibili)
    random.seed()

    # Carica dati
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

    # Crea assegnazioni casuali
    assignments = assign_random_apartments(cleaners, apartments)

    if not assignments:
        logging.error("Nessuna assegnazione creata")
        return

    # Salva risultati
    save_assignments(assignments)
    save_detailed_report(assignments)

    logging.info("=== ALGORITMO COMPLETATO CON SUCCESSO ===")
    logging.info(f"Totale assegnazioni create: {len(assignments)}")

    # Statistiche finali
    total_apartments_assigned = sum(len(assignment['apartments']) for assignment in assignments)
    logging.info(f"Appartamenti totali assegnati: {total_apartments_assigned}")
    logging.info(f"Media appartamenti per cleaner: {total_apartments_assigned / len(assignments):.1f}")


if __name__ == '__main__':
    main()