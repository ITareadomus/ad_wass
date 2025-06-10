import json
import random
from datetime import datetime


def load_cleaners():
    """Carica i cleaner dal file sel_cleaners.json"""
    try:
        with open('data/sel_cleaners.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('cleaners', [])
    except FileNotFoundError:
        print("Errore: File data/sel_cleaners.json non trovato")
        return []


def load_apartments():
    """Carica gli appartamenti dal file modello_apt.json"""
    try:
        with open('data/modello_apt.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('apt', [])
    except FileNotFoundError:
        print("Errore: File data/modello_apt.json non trovato")
        return []


def create_simple_assignments(cleaners, apartments):
    """Crea assegnazioni semplici: 3 appartamenti per cleaner con priorità casuali"""
    assignments = []
    available_apartments = apartments.copy()

    # Mescola gli appartamenti per renderli casuali
    random.shuffle(available_apartments)

    for cleaner in cleaners:
        # Prendi fino a 3 appartamenti per questo cleaner
        assigned_apartments = []

        for i in range(3):
            if available_apartments:
                apartment = available_apartments.pop(0)

                # Assegna priorità casuale da 1 a 3
                apartment['priority'] = random.randint(1, 3)

                assigned_apartments.append(apartment)

        if assigned_apartments:
            assignment = {
                'cleaner_id': cleaner['id'],
                'name': cleaner['name'],
                'lastname': cleaner['lastname'],
                'role': cleaner['role'],
                'sequence_details': assigned_apartments
            }
            assignments.append(assignment)

    return assignments


def save_assignments(assignments):
    """Salva le assegnazioni nel file data/assignments.json"""
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'assignments': assignments,
        'total_assignments': len(assignments)
    }

    with open('data/assignments.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Assegnazioni salvate in data/assignments.json - {len(assignments)} assegnazioni create")


def main():
    """Funzione principale"""
    print("=== ALGORITMO SEMPLICE ===")

    # Carica dati
    cleaners = load_cleaners()
    apartments = load_apartments()

    if not cleaners:
        print("Errore: Nessun cleaner trovato")
        return

    if not apartments:
        print("Errore: Nessun appartamento trovato")
        return

    print(f"Cleaner caricati: {len(cleaners)}")
    print(f"Appartamenti caricati: {len(apartments)}")

    # Crea assegnazioni casuali
    assignments = create_simple_assignments(cleaners, apartments)

    # Salva risultati
    save_assignments(assignments)

    print("=== COMPLETATO ===")
    print(f"Totale assegnazioni create: {len(assignments)}")

    # Stampa riepilogo
    for assignment in assignments:
        print(f"- {assignment['name']} {assignment['lastname']}: {len(assignment['sequence_details'])} appartamenti")


if __name__ == '__main__':
    main()