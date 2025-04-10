import json
import mysql.connector

# Carica configurazione dal file JSON
with open("modello.json", "r") as f:
    config = json.load(f)

db_config = config["db_config"]

# Connessione al database
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor(dictionary=True)

# Esegui la query per prendere i parametri dei cleaners
cursor.execute("""
    SELECT name, lastname, user_role_id, active
    FROM app_users 
    WHERE user_role_id IN (7, 15) AND active = 1;
""")
results = cursor.fetchall()


cursor.close()
connection.close()

# Predefiniamo i parametri statici
static_params = {
    "name": None,
    "lastname": None,
    "role": None,       
    "active": False,          
    "ranking": None,         
    "counter_hours": 0.0,     
    "counter_days": 0,        
    "available": False        
}

cleaners_data = []
for cleaner in results:

    cleaner_data = {
        "name": cleaner.get("name", static_params["name"]),
        "lastname": cleaner.get("lastname", static_params["lastname"]),
        "role": "Premium" if cleaner.get("user_role_id") == 15 else "Standard" if cleaner.get("user_role_id") == 7 else static_params["role"],
        "active": True if cleaner.get("active") == 1 else static_params["active"],
        "ranking": static_params["ranking"],
        "counter_hours": static_params["counter_hours"],
        "counter_days": static_params["counter_days"],
        "available": static_params["available"]
    }
    cleaners_data.append(cleaner_data)

# Aggiorna il JSON con i cleaners
config["cleaners"] = cleaners_data

# Sovrascrive il file modello.json con i dati aggiornati
with open("modello.json", "w") as f:
    json.dump(config, f, indent=4)

print(f"Aggiornato modello.json con {len(results)} cleaners.")

