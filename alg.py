import random
import mysql.connector
from collections import defaultdict

DB_CONFIG = {
    "host": "139.59.132.41",
    "user": "admin",
    "password": "ed329a875c6c4ebdf4e87e2bbe53a15771b5844ef6606dde",
    "database": "adam"
}

def test_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("Connessione al database riuscita!")
        conn.close()
    except mysql.connector.Error as err:
        print(f"Errore di connessione al database: {err}")

def fetch_cleaners_from_db():
    """Recupera nome, cognome e tipo dei cleaners dal database."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT name, lastname, user_role_id FROM app_users WHERE user_role_id IN (7, 15) AND active = 1;"
        cursor.execute(query)
        cleaners = cursor.fetchall()

        cursor.close()
        connection.close()

        return [{
            "name": f"{cleaner['name']} {cleaner['lastname']}", 
            "type": "Premium" if cleaner['user_role_id'] == 15 else "Standard", 
            "location": (random.randint(0, 100), random.randint(0, 100))
        } for cleaner in cleaners]
    
    except mysql.connector.Error as err:
        print(f"Errore nella connessione al DB: {err}")
        return []

def fetch_apartments_from_db():
    """Recupera gli appartamenti attivi dal database."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT id, name, address1, customer_id, lat, lng FROM app_structures WHERE active = 1;"
        cursor.execute(query)
        apartments = cursor.fetchall()

        cursor.close()
        connection.close()

        return apartments
    
    except mysql.connector.Error as err:
        print(f"Errore nella connessione al DB: {err}")
        return []

def generate_mock_apartments():
    return [
        {"id": i, "priority": random.randint(1, 5), "type": "Premium" if i % 2 == 0 else "Standard", 
         "location": (random.randint(0, 100), random.randint(0, 100)), "time": random.uniform(1, 3)}
        for i in range(101, 201)
    ]

def sort_by_priority(apartments):
    return sorted(apartments, key=lambda x: x["priority"], reverse=True)

def filter_by_type(items, type_value):
    return [item for item in items if item["type"] == type_value]

def euclidean_distance(loc1, loc2):
    return ((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2) ** 0.5

def assign_apartments(apartments, cleaners):
    assignments = defaultdict(list)
    
    for apt in apartments:
        available_cleaners = [c for c in cleaners if c["type"] == apt["type"] or c["type"] == "Premium"]
        if not available_cleaners:
            continue
        
        cleaner = min(available_cleaners, key=lambda c: (len(assignments[c["name"]]), euclidean_distance(c["location"], apt["location"])) )
        assignments[cleaner["name"]].append(apt)
    
    return assignments

def main():
    cleaners = fetch_cleaners_from_db()
    apartments = fetch_apartments_from_db()
    
    if cleaners:
        print("Lista cleaners dal database:")
        for cleaner in cleaners:
            print(f"{cleaner['name']} ({cleaner['type']})", end=", ")
        print("\n")
    
    if apartments:
        print("Lista appartamenti dal database:")
        for apt in apartments:
            print(f"ID: {apt['id']}, Nome: {apt['name']}, Indirizzo: {apt['address1']}, Cliente: {apt['customer_id']}, Lat: {apt['lat']}, Lng: {apt['lng']}")
    
    generated_apartments = generate_mock_apartments()
    
    apartments_premium = sort_by_priority(filter_by_type(generated_apartments, "Premium"))
    apartments_standard = sort_by_priority(filter_by_type(generated_apartments, "Standard"))
    
    assignments_premium = assign_apartments(apartments_premium, cleaners)
    assignments_standard = assign_apartments(apartments_standard, cleaners)
    
    print("Assegnazioni Premium:")
    for cleaner, apts in assignments_premium.items():
        print(f"{cleaner}: {[apt['id'] for apt in apts]}")
    
    print("\nAssegnazioni Standard:")
    for cleaner, apts in assignments_standard.items():
        print(f"{cleaner}: {[apt['id'] for apt in apts]}")

if __name__ == "__main__":
    main()
