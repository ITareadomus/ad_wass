import json
import mysql.connector
from datetime import datetime, timedelta

# Carica configurazione dal file JSON
with open("modello_cleaner.json", "r") as f:
    config = json.load(f)

db_config = config["db_config"]

# Connessione al database
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor(dictionary=True)

# Esegui la query per prendere i parametri dei cleaners
cursor.execute("""
    SELECT id, name, lastname, user_role_id, active
    FROM app_users 
    WHERE user_role_id IN (7, 15) AND active = 1;
""")
results = cursor.fetchall()

# Calcola la data di domani
tomorrow = (datetime.now() + timedelta(days=1)).date()

# Predefiniamo i parametri statici
static_params = {
    "name": None,
    "lastname": None,
    "role": None,       
    "active": False,          
    "ranking": 0,         
    "counter_hours": 0.0,     
    "counter_days": 0,        
    "available": False,   
    "contract_type": None
}

cleaners_data = []
for cleaner in results:
    # Controlla se il cleaner è presente nella tabella app_attendance per domani
    cursor.execute("""
        SELECT 1
        FROM app_attendance
        WHERE user_id = %s AND %s BETWEEN start_date AND end_date;
    """, (cleaner["id"], tomorrow))
    attendance_result = cursor.fetchone()

    cleaner_data = {
        "name": cleaner.get("name", static_params["name"]),
        "lastname": cleaner.get("lastname", static_params["lastname"]),
        "role": "Premium" if cleaner.get("user_role_id") == 15 else "Standard" if cleaner.get("user_role_id") == 7 else static_params["role"],
        "active": True if cleaner.get("active") == 1 else static_params["active"],
        "ranking": static_params["ranking"],
        "counter_hours": static_params["counter_hours"],
        "counter_days": static_params["counter_days"],
        "available": True if not attendance_result else False,
        "contract_type": static_params["contract_type"]
    }
    cleaners_data.append(cleaner_data)

cursor.close()
connection.close()

# Aggiorna il JSON con i cleaners
config["cleaners"] = cleaners_data

# Sovrascrive il file modello.json con i dati aggiornati
with open("modello_cleaner.json", "w") as f:
    json.dump(config, f, indent=4)

print(f"Aggiornato modello_cleaner.json con {len(results)} cleaners.")

