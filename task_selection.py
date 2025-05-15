import json
import mysql.connector
from datetime import datetime, date

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

# Caricamento configurazione da file JSON
try:
    with open("modello_apt.json", "r") as f:
        config = json.load(f)
except json.decoder.JSONDecodeError as e:
    print(f"Errore nel caricamento del JSON: {e}")
    config = {"apt": []}

# Configurazione del database
db_config = {
    "host": "139.59.132.41",
    "user": "admin",
    "password": "ed329a875c6c4ebdf4e87e2bbe53a15771b5844ef6606dde",
    "database": "adam"
}

# Connessione al database
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor(dictionary=True)

# Query con JOIN su structures e recupero anche customer_id come client_id
cursor.execute("""
    SELECT 
        h.id,
        h.structure_id,
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
    WHERE h.checkout = DATE_ADD(CURDATE(), INTERVAL 1 DAY)
""")
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
    small_equipment = True if structure_type_id in (1, 2) else static_params["small_equipment"]
    apt_entry = {
        "task_id": apt.get("id", static_params["task_id"]),
        "structure_id": apt.get("structure_id", static_params["structure_id"]),
        "client_id": apt.get("client_id", static_params["client_id"]),
        "type": "Premium" if apt.get("premium") == 1 else "Standard",
        "address": apt.get("address", static_params["address"]),
        "lat": normalize_coord(apt.get("lat")),
        "lng": normalize_coord(apt.get("lng")),
        "cleaning_time": static_params["cleaning_time"],
        "checkin": date_to_str(apt.get("checkin")) if apt.get("checkin") else static_params["checkin"],
        "checkout": date_to_str(apt.get("checkout")) if apt.get("checkout") else static_params["checkout"],
        "checkin_time": varchar_to_str(apt.get("checkin_time")) if apt.get("checkin_time") else static_params["checkin_time"],
        "checkout_time": varchar_to_str(apt.get("checkout_time")) if apt.get("checkout_time") else static_params["checkout_time"],
        "pax_in": apt.get("pax_in", static_params["pax_in"]),
        "pax_out": apt.get("pax_out", static_params["pax_out"]),
        "small_equipment": small_equipment,
    }
    apt_data.append(apt_entry)

# Aggiorna la configurazione
config["apt"] = apt_data

# Salva nel file JSON
def custom_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(f'Tipo {obj.__class__.__name__} non serializzabile')

with open("modello_apt.json", "w") as f:
    json.dump(config, f, indent=4, default=custom_serializer)

print(f"Aggiornato modello_apt.json con {len(results)} appartamenti.")
