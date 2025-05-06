import googlemaps

# Inserisci qui la tua Google Maps API Key
API_KEY = 'AIzaSyBRKGlNnryWd0psedJholmVPlaxQUmSlY0'  # TODO: sostituisci con la tua chiave reale

gmaps = googlemaps.Client(key=API_KEY)

def calcola_distanza(lat1, lng1, lat2, lng2, mode='walking'):
    """
    Calcola la distanza e il tempo di percorrenza tra due coordinate geografiche.

    Args:
        lat1 (float): Latitudine del punto di partenza.
        lng1 (float): Longitudine del punto di partenza.
        lat2 (float): Latitudine del punto di arrivo.
        lng2 (float): Longitudine del punto di arrivo.
        mode (str): Modalità di trasporto ('driving', 'walking', 'bicycling', 'transit').

    Returns:
        dict: Dizionario con 'distanza_testo', 'distanza_metri', 'durata', oppure None in caso di errore.
    """
    origine = f"{lat1},{lng1}"
    destinazione = f"{lat2},{lng2}"

    try:
        result = gmaps.distance_matrix(origins=[origine],
                                       destinations=[destinazione],
                                       mode=mode,
                                       units='metric')

        elemento = result['rows'][0]['elements'][0]

        if elemento['status'] != 'OK':
            raise ValueError(f"Errore nella risposta della Distance Matrix: {elemento['status']}")

        distanza_testo = elemento['distance']['text']
        distanza_valore = elemento['distance']['value']  # in metri
        durata = elemento['duration']['text']

        return {
            'distanza_testo': distanza_testo,
            'distanza_metri': distanza_valore,
            'durata': durata
        }

    except Exception as e:
        print("Errore nel calcolo della distanza:", e)
        return None

# ESEMPIO USO (decommentare per test)
# if __name__ == "__main__":
#     lat1, lng1 = 45.4474306, 9.1559278  # Punto 1
#     lat2, lng2 = 45.4549824, 9.1722022  # Punto 2
#
#     distanza = calcola_distanza(lat1, lng1, lat2, lng2)
#     if distanza:
#         print("Distanza:", distanza['distanza_testo'])
#         print("Durata:", distanza['durata'])
