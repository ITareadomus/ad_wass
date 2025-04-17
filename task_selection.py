import json
import mysql.connector
from datetime import datetime, date

# Funzione per convertire i campi di tipo date e datetime in stringhe
def date_to_str(value):
    if isinstance(value, (datetime, date)):  # Gestisce sia datetime che date
        return value.strftime('%Y-%m-%d')  # Converte in formato stringa YYYY-MM-DD
    return value  # Ritorna il valore così com'è se non è un oggetto datetime o date

# Funzione per verificare e restituire il valore di tipo stringa
def varchar_to_str(value):
    if value is None:
        return None  # Mantiene None per i campi NULL
    return str(value)  # Converte in stringa nel caso in cui il campo è già un varchar

# Carica configurazione dal file JSON con gestione degli errori
try:
    with open("modello_apt.json", "r") as f:
        config = json.load(f)
except json.decoder.JSONDecodeError as e:
    print(f"Errore nel caricamento del JSON: {e}")
    config = {"apt": []}  # Imposta un valore di default se il file è vuoto o malformato

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

# Esegui la query per prendere i parametri degli appartamenti
cursor.execute("""
    SELECT id, structure_id, checkin, checkout, checkin_time, checkout_time
    FROM app_housekeeping 
    WHERE checkout = CURDATE() + INTERVAL 1 DAY
""")
results = cursor.fetchall()

cursor.close()
connection.close()

# Predefiniamo i parametri statici, tutti settati su None
static_params = {
    "task_id": None,
    "structure_id": None,
    "client_id": None,
    "type": None,       
    "address": None,          
    "lat": None,         
    "lng": None,     
    "cleaning_time": None,        
    "checkin": None,  # Impostato a None
    "checkout": None, 
    "checkin_time": None,  # Impostato a None
    "checkout_time": None,  # Impostato a None
    "pax_in": None,
    "pax_out": None,      
}

# Lista per raccogliere i dati degli appartamenti
apt_data = []

# Cicla sui risultati della query e prepara i dati
for apt in results:
    # Usa il valore di static_params se il valore dal db è NULL
    apt_entry = {
        "task_id": apt.get("id") if apt.get("id") is not None else static_params["task_id"],
        "structure_id": apt.get("structure_id") if apt.get("structure_id") is not None else static_params["structure_id"],
        "client_id": static_params["client_id"],  # Sempre statico in questo caso
        "type": static_params["type"],  # Sempre statico in questo caso
        "address": static_params["address"],  # Sempre statico in questo caso
        "lat": static_params["lat"],  # Sempre statico in questo caso
        "lng": static_params["lng"],  # Sempre statico in questo caso
        "cleaning_time": static_params["cleaning_time"],  # Sempre statico in questo caso
        "checkin": date_to_str(apt.get("checkin")) if apt.get("checkin") is not None else static_params["checkin"],
        "checkout": date_to_str(apt.get("checkout")) if apt.get("checkout") is not None else static_params["checkout"],
        "checkin_time": varchar_to_str(apt.get("checkin_time")) if apt.get("checkin_time") is not None else static_params["checkin_time"],
        "checkout_time": varchar_to_str(apt.get("checkout_time")) if apt.get("checkout_time") is not None else static_params["checkout_time"],
        "pax_in": static_params["pax_in"],  # Sempre statico in questo caso
        "pax_out": static_params["pax_out"],  # Sempre statico in questo caso
    }
    apt_data.append(apt_entry)

# Aggiorna il JSON con i dati degli appartamenti
config["apt"] = apt_data

# Funzione per serializzare correttamente le date nel JSON
def custom_serializer(obj):
    if isinstance(obj, (datetime, date)):  # Gestisce datetime e date
        return obj.strftime('%Y-%m-%d')
    raise TypeError(f'Tipo {obj.__class__.__name__} non serializzabile')

# Sovrascrive il file modello_apt.json con i dati aggiornati
with open("modello_apt.json", "w") as f:
    json.dump(config, f, indent=4, default=custom_serializer)

print(f"Aggiornato modello_apt.json con {len(results)} appartamenti.")
