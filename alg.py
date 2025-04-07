import random
import mysql.connector
import requests
from collections import defaultdict

# Configurazione database
DB_CONFIG = {
    "host": "139.59.132.41",
    "user": "admin",
    "password": "ed329a875c6c4ebdf4e87e2bbe53a15771b5844ef6606dde",
    "database": "adam"
}

# API Key di Google Maps
GOOGLE_API_KEY = "AIzaSyBRKGlNnryWd0psedJholmVPlaxQUmSlY0"

class Apartment:
    def __init__(self, id, name, address, customer_id, lat, lng, apt_type):
        self.id = id
        self.name = name
        self.address = address
        self.customer_id = customer_id
        self.lat = lat
        self.lng = lng
        self.type = apt_type

    def __repr__(self):
        return f"Apartment(ID: {self.id}, Type: {self.type})"

def fetch_apartments_from_db():
    """Recupera gli appartamenti attivi dal database e li inserisce in oggetti Apartment."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT id, name, address1, customer_id, lat, lng FROM app_structures WHERE active = 1;"
        cursor.execute(query)
        apartments = cursor.fetchall()

        cursor.close()
        connection.close()

        return [Apartment(
            apt["id"], apt["name"], apt["address1"], apt["customer_id"], apt["lat"], apt["lng"],
            "Premium" if apt["id"] % 2 == 0 else "Standard"
        ) for apt in apartments]
    
    except mysql.connector.Error as err:
        print(f"Errore nella connessione al DB: {err}")
        return []

def get_driving_distance(origin, destination):
    """Calcola la distanza su strada tra due coordinate usando Google Maps API."""
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin[0]},{origin[1]}",  
        "destinations": f"{destination[0]},{destination[1]}",
        "key": GOOGLE_API_KEY,
        "mode": "driving"
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200 and data["rows"]:
        try:
            distance_meters = data["rows"][0]["elements"][0]["distance"]["value"]
            return distance_meters / 1000  # Converti in km
        except KeyError:
            return float('inf')
    else:
        return float('inf')

def assign_apartments(apartments):
    """Assegna gli appartamenti in base alla distanza tra di loro."""
    assignments = defaultdict(list)
    
    # Calcoliamo la distanza tra appartamenti consecutivi
    for i in range(len(apartments) - 1):
        apt1 = apartments[i]
        apt2 = apartments[i + 1]
        
        # Calcola la distanza tra due appartamenti consecutivi
        distance = get_driving_distance((apt1.lat, apt1.lng), (apt2.lat, apt2.lng))
        
        # Aggiungi l'appartamento alla lista in base alla distanza
        assignments[apt1.name].append(apt2.id)
    
    return assignments

def main():
    apartments = fetch_apartments_from_db()
    
    if apartments:
        print("Lista appartamenti dal database:")
        for apt in apartments:
            print(f"ID: {apt.id}, Nome: {apt.name}, Indirizzo: {apt.address}, Cliente: {apt.customer_id}, Lat: {apt.lat}, Lng: {apt.lng}")
    
    assignments = assign_apartments(apartments)
    
    print("\nAssegnazioni Appartamenti -> ID Appartamenti Successivi:")
    for apt_name, apts in assignments.items():
        print(f"{apt_name}: {apts}")

if __name__ == "__main__":
    main()
