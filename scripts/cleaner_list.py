import json
import mysql.connector
from datetime import datetime, timedelta

# Configurazione del database (puoi metterla qui direttamente o caricarla da un altro file se vuoi)
db_config = {
    "host": "139.59.132.41",
    "user": "admin",
    "password": "ed329a875c6c4ebdf4e87e2bbe53a15771b5844ef6606dde",
    "database": "adamdb"
}

# Crea il modello base da zero
config = {"db_config": db_config, "cleaners": []}

#ho aggiunto delle colonne nella tabella app_users in cui ho aggiunto un campo per il minimo ore e un altro per il tipo di contratto

db_config = config["db_config"]

# Connessione al database
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor(dictionary=True)

# Esegui la query per prendere i parametri dei cleaners
cursor.execute("""
    SELECT id, name, lastname, user_role_id, active, contract_type_id
    FROM app_users 
    WHERE user_role_id IN (7, 15) AND active = 1;
""")
results = cursor.fetchall()

# Calcola la data di domani
tomorrow = (datetime.now() + timedelta(days=1)).date()

# Predefiniamo i parametri statici
static_params = {
    "id": None,  # Aggiunto il campo id
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


def get_monthly_hours(cursor, user_id):
    """Somma le duration (VARCHAR) anche se sono in formato 'H:M'."""
    now = datetime.now()
    first_day = now.replace(day=1).date()
    last_day = (now.replace(month=now.month % 12 + 1, day=1) -
                timedelta(days=1)).date()
    cursor.execute(
        """
        SELECT duration
        FROM app_housekeeping_report
        WHERE user_id = %s
          AND updated_at BETWEEN %s AND %s
    """, (user_id, first_day, last_day))
    durations = cursor.fetchall()
    print(
        f"user_id={user_id} durations={[row['duration'] for row in durations]}"
    )
    total = 0.0
    for row in durations:
        val = row["duration"]
        if not val:
            continue
        val = val.strip()
        if ":" in val:  # formato ore:minuti
            try:
                h, m = val.split(":")
                total += int(h) + int(m) / 60
            except Exception:
                continue
        else:
            try:
                total += float(val)
            except Exception:
                continue
    return round(total, 2)


def get_consecutive_days(cursor, user_id):
    """Conta i giorni lavorati consecutivamente fino a oggi."""
    today = datetime.now().date()
    # Prendi tutte le date in cui ha lavorato, in ordine decrescente
    cursor.execute(
        """
        SELECT DISTINCT DATE(updated_at) as work_date
        FROM app_housekeeping_report
        WHERE user_id = %s AND updated_at <= %s
        ORDER BY work_date DESC
    """, (user_id, today))
    dates = [row["work_date"] for row in cursor.fetchall()]
    if not dates or dates[0] != today:
        return 0  # Non ha lavorato oggi, contatore a 0

    # Conta i giorni consecutivi a partire da oggi
    counter = 1
    prev_day = today
    for d in dates[1:]:
        if d == prev_day - timedelta(days=1):
            counter += 1
            prev_day = d
        else:
            break
    return counter


cleaners_data = []
for cleaner in results:
    # Controlla se il cleaner è presente nella tabella app_attendance per domani
    cursor.execute(
        """
        SELECT 1
        FROM app_attendance
        WHERE user_id = %s AND %s BETWEEN start_date AND stop_date;
    """, (cleaner["id"], tomorrow))
    attendance_result = cursor.fetchone()

    # Mappa contract_type_id numerico a lettera
    contract_type_db = cleaner.get("contract_type_id",
                                   static_params["contract_type"])
    if contract_type_db == 1:
        contract_type = "A"
    elif contract_type_db == 2:
        contract_type = "B"
    elif contract_type_db == 3:
        contract_type = "C"
    else:
        contract_type = contract_type_db  # mantiene None o altro valore se non 1/2/3

    counter_hours = get_monthly_hours(cursor, cleaner["id"])
    counter_days = get_consecutive_days(cursor, cleaner["id"])
    cleaner_data = {
        "id":
        cleaner.get("id", static_params["id"]),  # Aggiunto il campo id
        "name":
        cleaner.get("name", static_params["name"]),
        "lastname":
        cleaner.get("lastname", static_params["lastname"]),
        "role":
        "Premium" if cleaner.get("user_role_id") == 15 else "Standard"
        if cleaner.get("user_role_id") == 7 else static_params["role"],
        "active":
        True if cleaner.get("active") == 1 else static_params["active"],
        "ranking":
        static_params["ranking"],
        "counter_hours":
        counter_hours,
        "counter_days":
        counter_days,
        "available":
        True if not attendance_result else False,
        "contract_type":
        contract_type
    }
    cleaners_data.append(cleaner_data)

cursor.close()
connection.close()

# Aggiorna il JSON con i cleaners
config["cleaners"] = cleaners_data

# Sovrascrive il file modello_cleaners.json con i dati aggiornati nella cartella data
with open("data/modello_cleaners.json", "w") as f:
    json.dump(config, f, indent=4)

print(f"Aggiornato data/modello_cleaners.json con {len(results)} cleaners.")
