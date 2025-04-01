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
    """Recupera nome e cognome dei cleaners dal database dove user_role_id è 7 o 15."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT name, lastname FROM app_users WHERE user_role_id IN (7, 15) AND active = 1;"
        cursor.execute(query)
        cleaners = cursor.fetchall()

        cursor.close()
        connection.close()

        return [f"{cleaner['name']} {cleaner['lastname']}" for cleaner in cleaners]

    except mysql.connector.Error as err:
        print(f"Errore nella connessione al DB: {err}")
        return []


def generate_mock_data():
    cleaners = [
        {"id": i, "name": f"Cleaner_{i}", "type": "Premium" if i % 2 == 0 else "Standard", "location": (random.randint(0, 100), random.randint(0, 100))}
        for i in range(1, 21)
    ]
    
    apartments = [
        {"id": i, "priority": random.randint(1, 5), "type": "Premium" if i % 2 == 0 else "Standard", 
         "location": (random.randint(0, 100), random.randint(0, 100)), "time": random.uniform(1, 3)}
        for i in range(101, 201)
    ]
    return cleaners, apartments

def sort_by_priority(apartments):
    return sorted(apartments, key=lambda x: x["priority"], reverse=True)

def filter_by_type(items, type_value):
    return [item for item in items if item["type"] == type_value]

def euclidean_distance(loc1, loc2):
    return ((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2) ** 0.5

def find_best_next_apartment(cleaner, available_apts, current_apt, use_gmaps=False):
    if not available_apts:
        return None
    
    available_apts = [apt for apt in available_apts if apt["type"] == cleaner["type"] or cleaner["type"] == "Premium"]
    if not available_apts:
        return None
    
    distance_func = gmaps_distance if use_gmaps else euclidean_distance
    return min(available_apts, key=lambda apt: distance_func(current_apt["location"], apt["location"]))

def assign_apartments(apartments, cleaners, use_gmaps=False):
    assignments = defaultdict(list)
    
    for apt in apartments:
        available_cleaners = [c for c in cleaners if c["type"] == apt["type"] or c["type"] == "Premium"]
        if not available_cleaners:
            continue
        
        cleaner = min(available_cleaners, key=lambda c: (len(assignments[c["name"]]), euclidean_distance(c["location"], apt["location"])) if not use_gmaps else (len(assignments[c["name"]]), gmaps_distance(c["location"], apt["location"])))
        assignments[cleaner["name"]].append(apt)
    
    remaining_apartments = [apt for apt in apartments if apt not in sum(assignments.values(), [])]
    for cleaner in cleaners:
        if cleaner["name"] in assignments and assignments[cleaner["name"]]:
            first_apt = assignments[cleaner["name"]][0]
            next_apt = find_best_next_apartment(cleaner, remaining_apartments, first_apt, use_gmaps)
            if next_apt:
                assignments[cleaner["name"]].append(next_apt)
                remaining_apartments.remove(next_apt)
    
    return assignments

def main():
    cleaners_from_db = fetch_cleaners_from_db()

    if cleaners_from_db:
        print("Lista cleaners dal database:")
        for cleaner in cleaners_from_db:
            print(cleaner, end=", ")
        print("\n")

    cleaners, apartments = generate_mock_data()
    
    apartments_premium = sort_by_priority(filter_by_type(apartments, "Premium"))
    apartments_standard = sort_by_priority(filter_by_type(apartments, "Standard"))
    
    cleaners_premium = filter_by_type(cleaners, "Premium")
    cleaners_standard = filter_by_type(cleaners, "Standard")
    
    assignments_premium = assign_apartments(apartments_premium, cleaners_premium)
    assignments_standard = assign_apartments(apartments_standard, cleaners_standard)
    
    print("Assegnazioni Premium:")
    for cleaner, apts in assignments_premium.items():
        print(f"{cleaner}: {[apt['id'] for apt in apts]}")
    
    print("\nAssegnazioni Standard:")
    for cleaner, apts in assignments_standard.items():
        print(f"{cleaner}: {[apt['id'] for apt in apts]}")

if __name__ == "__main__":
    main()

