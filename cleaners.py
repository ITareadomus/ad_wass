import json

# Carica i dati dal file JSON
with open("modello_cleaner.json", "r") as f:
    data = json.load(f)

cleaners = data.get("cleaners", [])

# Filtra i cleaner attivi e disponibili
eligible_cleaners = [c for c in cleaners if c.get("active") and c.get("available")]

# Ordina per ranking decrescente, poi per counter_days crescente
sorted_cleaners = sorted(
    eligible_cleaners,
    key=lambda x: (-x.get("ranking", 0), x.get("counter_days", 0))
)

# Separa i cleaner per ruolo
premium_cleaners = [c for c in sorted_cleaners if c.get("role", "").lower() == "premium"]
standard_cleaners = [c for c in sorted_cleaners if c.get("role", "").lower() == "standard"]

# Seleziona fino a 10 cleaner per tipo
selected_premium = premium_cleaners[:10]
selected_standard = standard_cleaners[:10]

# Unione finale
selected_cleaners = selected_premium + selected_standard

# Scrivi l'output nel file JSON
with open("selected_cleaners.json", "w") as f:
    json.dump({"selected_cleaners": selected_cleaners}, f, indent=4)

print(f"Selezionati {len(selected_cleaners)} cleaner e salvati in 'selected_cleaners.json'")
