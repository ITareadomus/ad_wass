# route_optimizer.py

import logging
import googlemaps
from datetime import datetime

# Inizializza il client con la tua API Key
gmaps = googlemaps.Client(key="AIzaSyBRKGlNnryWd0psedJholmVPlaxQUmSlY0")

def optimize_route(pkg, mode="walking"):
    """
    Dato un pacchetto pkg (lista di dict con 'lat','lng'),
    restituisce lo stesso pkg riordinato secondo l'ottimizzazione Google.
    """
    if len(pkg) < 2:
        return pkg

    # Costruisci gli indirizzi in formato "lat,lng"
    coords = [f"{a['lat']},{a['lng']}" for a in pkg]
    origin = coords[0]
    waypoints = ["optimize:true"] + coords[1:]

    try:
        res = gmaps.directions(
            origin,
            origin,
            mode=mode,
            departure_time=datetime.now(),
            waypoints=waypoints
        )
        order = res[0]['waypoint_order']
        # ricostruisci la lista: origin fisso in testa + il resto nell'ordine ottimizzato
        optimized = [pkg[0]] + [pkg[i+1] for i in order]
        return optimized

    except Exception as e:
        logging.error(f"Errore ottimizzazione route: {e}")
        # se fallisce, torna il pacchetto originale
        return pkg
