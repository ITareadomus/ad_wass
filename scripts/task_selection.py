try:
    with open("data/modello_apt.json", "r") as f:
        config = json.load(f)
except json.decoder.JSONDecodeError as e:
    print(f"Errore nel caricamento del JSON: {e}")
    config = {"apt": []}
try:
    with open("data/modello_apt.json", "r") as f:
        config = json.load(f)
except json.decoder.JSONDecodeError as e:
    print(f"Errore nel caricamento del JSON: {e}")
    config = {"apt": []}
with open("data/modello_apt.json", "w") as f:
    json.dump(config, f, indent=4, default=custom_serializer)

print(f"Aggiornato data/modello_apt.json con {len(results)} appartamenti.")