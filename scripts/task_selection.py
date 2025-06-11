# Applied indentation fix in cleaner_selection.py

import json
import mysql.connector
import sys
from datetime import datetime, date, timedelta


# Funzione per convertire i campi di tipo date e datetime in stringhe
def date_to_str(value):
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d')
    return value


# Funzione per convertire i valori VARCHAR (anche None) in stringa
def varchar_to_str(value):
    if value is None:
        return None
    return str(value)


def normalize_coord(coord):
    if coord is None:
        return None
    return str(coord).replace(',', '.').strip()


def get_apartments_for_date(selected_date):
    """
    Carica appartamenti dal database per una data specifica
    """
    # Configurazione del database
    db_config = {
        "host": "139.59.132.41",
        "user": "admin",
        "password": "ed329a875c6c4ebdf4e87e2bbe53a15771b5844ef6606dde",
        "database": "adamdb"
    }

    # Connessione al database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)

    # Query con JOIN su structures e recupero anche customer_id come client_id, usando logistic_code come structure_id
    # Filtra per la data specifica di checkout
    cursor.execute("""
        SELECT 
            h.id,
            s.logistic_code AS structure_id,
            h.checkin,
            h.checkout,
            h.checkin_time,
            h.checkout_time,
            s.address1 AS address,
            s.lat,
            s.lng,
            h.checkin_pax AS pax_in,
            h.checkout_pax AS pax_out,
            s.premium AS premium,
            s.customer_id AS client_id,
            s.structure_type_id 
        FROM app_housekeeping h
        JOIN app_structures s ON h.structure_id = s.id
        WHERE h.checkout = %s
    """, (selected_date,))
    results = cursor.fetchall()

    cursor.close()
    connection.close()

    # Parametri statici
    static_params = {
        "task_id": None,
        "structure_id": None,
        "client_id": None,
        "type": "Standard",
        "address": None,
        "lat": None,
        "lng": None,
        "cleaning_time": None,
        "checkin": None,
        "checkout": None,
        "checkin_time": None,
        "checkout_time": None,
        "pax_in": None,
        "pax_out": None,
        "small_equipment": False,
    }

    # Prepara la lista dei dati appartamenti
    apt_data = []

    for apt in results:
        structure_type_id = apt.get("structure_type_id", None)
        small_equipment = True if structure_type_id == 1 else static_params[
            "small_equipment"]
        apt_entry = {
            "task_id":
            apt.get("id", static_params["task_id"]),
            "structure_id":
            apt.get("structure_id", static_params["structure_id"]),
            "client_id":
            apt.get("client_id", static_params["client_id"]),
            "type":
            "Premium" if apt.get("premium") == 1 else "Standard",
            "address":
            apt.get("address", static_params["address"]),
            "lat":
            normalize_coord(apt.get("lat")),
            "lng":
            normalize_coord(apt.get("lng")),
            "cleaning_time":
            static_params["cleaning_time"],
            "checkin":
            date_to_str(apt.get("checkin"))
            if apt.get("checkin") else static_params["checkin"],
            "checkout":
            date_to_str(apt.get("checkout"))
            if apt.get("checkout") else static_params["checkout"],
            "checkin_time":
            varchar_to_str(apt.get("checkin_time"))
            if apt.get("checkin_time") else static_params["checkin_time"],
            "checkout_time":
            varchar_to_str(apt.get("checkout_time"))
            if apt.get("checkout_time") else static_params["checkout_time"],
            "pax_in":
            apt.get("pax_in", static_params["pax_in"]),
            "pax_out":
            apt.get("pax_out", static_params["pax_out"]),
            "small_equipment":
            small_equipment,
        }
        apt_data.append(apt_entry)

    return apt_data, len(results)


def main():
    selected_date = None

    # Controlla i parametri della riga di comando
    if len(sys.argv) > 1:
        selected_date = sys.argv[1]
        print(f"Usando data specifica: {selected_date}")

    # Se non viene fornita una data, usa quella di domani (default)
    if not selected_date:
        tomorrow = datetime.now() + timedelta(days=1)
        selected_date = tomorrow.strftime("%Y-%m-%d")
        print(f"Usando data di default (domani): {selected_date}")

    # Carica i dati esistenti o crea una struttura vuota
    try:
        with open("data/modello_apt.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {"dates": {}}

    # Assicurati che la struttura contenga la chiave "dates"
    if "dates" not in existing_data:
        existing_data = {"dates": {}}

    # Carica appartamenti per la data specifica
    apt_data, apt_count = get_apartments_for_date(selected_date)

    # Aggiorna i dati per la data specifica
    existing_data["dates"][selected_date] = {
        "timestamp": datetime.now().isoformat(),
        "apt": apt_data,
        "total_apartments": apt_count,
        "date": selected_date
    }

    # Salva nel file JSON
    def custom_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime('%Y-%m-%d')
        raise TypeError(f'Tipo {obj.__class__.__name__} non serializzabile')

    with open("data/modello_apt.json", "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, default=custom_serializer, ensure_ascii=False)

    print(f"Aggiornato modello_apt.json con {apt_count} appartamenti per la data {selected_date}.")


if __name__ == "__main__":
    main()
`