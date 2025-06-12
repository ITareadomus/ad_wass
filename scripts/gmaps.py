import googlemaps

# Inserisci qui la tua Google Maps API Key
API_KEY = 'AIzaSyBRKGlNnryWd0psedJholmVPlaxQUmSlY0'  # TODO: sostituisci con la tua chiave reale

gmaps = googlemaps.Client(key=API_KEY)

def calcola_distanza(lat1, lng1, lat2, lng2, mode='walking', departure_time=None):
    """
    Calcola la distanza e il tempo di percorrenza tra due coordinate geografiche.

    Args:
        lat1 (float): Latitudine del punto di partenza.
        lng1 (float): Longitudine del punto di partenza.
        lat2 (float): Latitudine del punto di arrivo.
        lng2 (float): Longitudine del punto di arrivo.
        mode (str): Modalità di trasporto ('driving', 'walking', 'bicycling', 'transit').
        departure_time (int|datetime, opzionale): Timestamp o datetime di partenza.

    Returns:
        dict: Dizionario con 'distanza_testo', 'distanza_metri', 'durata' (in secondi), 'durata_testo', oppure None in caso di errore.
    """
    # Validazione input
    try:
        lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
    except (ValueError, TypeError):
        print(f"Errore: coordinate non valide - lat1:{lat1}, lng1:{lng1}, lat2:{lat2}, lng2:{lng2}")
        return None
    
    # Controllo coordinate valide
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        print(f"Errore: latitudini fuori range - lat1:{lat1}, lat2:{lat2}")
        return None
    
    if not (-180 <= lng1 <= 180 and -180 <= lng2 <= 180):
        print(f"Errore: longitudini fuori range - lng1:{lng1}, lng2:{lng2}")
        return None

    origine = f"{lat1},{lng1}"
    destinazione = f"{lat2},{lng2}"

    try:
        params = dict(
            origins=[origine],
            destinations=[destinazione],
            mode=mode,
            units='metric'
        )
        if departure_time is not None:
            params['departure_time'] = departure_time

        result = gmaps.distance_matrix(**params)

        # Verifica struttura risposta
        if not result.get('rows') or not result['rows'][0].get('elements'):
            print(f"Errore: risposta API malformata per {origine} -> {destinazione}")
            return None

        elemento = result['rows'][0]['elements'][0]

        if elemento['status'] != 'OK':
            print(f"Errore API Google Maps: {elemento['status']} per {origine} -> {destinazione}")
            return None

        distanza_testo = elemento['distance']['text']
        distanza_valore = elemento['distance']['value']  # in metri
        durata_testo = elemento['duration']['text']
        durata_valore = elemento['duration']['value']    # in secondi

        # Debug info
        print(f"Distanza calcolata: {origine} -> {destinazione} = {durata_testo} ({durata_valore}s)")

        return {
            'distanza_testo': distanza_testo,
            'distanza_metri': distanza_valore,
            'durata': durata_valore,      # in secondi!
            'durata_testo': durata_testo  # opzionale
        }

    except Exception as e:
        print(f"Errore nel calcolo della distanza da {origine} a {destinazione}: {e}")
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
