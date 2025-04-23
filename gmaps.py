import googlemaps

# Inserisci qui la tua Google Maps API Key
API_KEY = 'AIzaSyBRKGlNnryWd0psedJholmVPlaxQUmSlY0'
gmaps = googlemaps.Client(key=API_KEY)

def calcola_distanza(lat1, lon1, lat2, lon2):
    origine = f"{lat1},{lon1}"
    destinazione = f"{lat2},{lon2}"
    
    result = gmaps.distance_matrix(origins=[origine],
                                   destinations=[destinazione],
                                   mode='driving',  # puoi usare anche 'walking', 'bicycling', 'transit'
                                   units='metric')

    try:
        distanza_testo = result['rows'][0]['elements'][0]['distance']['text']
        distanza_valore = result['rows'][0]['elements'][0]['distance']['value']  # in metri
        durata = result['rows'][0]['elements'][0]['duration']['text']

        return {
            'distanza_testo': distanza_testo,
            'distanza_metri': distanza_valore,
            'durata': durata
        }
    except Exception as e:
        print("Errore nel calcolo della distanza:", e)
        return None

# Esempio
if __name__ == "__main__":
    lat1, lon1 = 45.4642, 9.1900  # Milano
    lat2, lon2 = 45.4064, 11.8768  # Padova

    distanza = calcola_distanza(lat1, lon1, lat2, lon2)
    if distanza:
        print("Distanza:", distanza['distanza_testo'])
        print("Durata:", distanza['durata'])
