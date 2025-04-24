import json
import math

# Caricamento del file JSON
with open("mock_apartments.json", "r") as f:
    config = json.load(f)

# Estrai la lista degli appartamenti
apartments = config.get("apt", [])

# Conta gli appartamenti per tipo
premium_apts = [apt for apt in apartments if apt.get("type") == "Premium"]
standard_apts = [apt for apt in apartments if apt.get("type") == "Standard"]

num_premium = len(premium_apts)
num_standard = len(standard_apts)

# Calcola i cleaner necessari (1 ogni 3 appartamenti, arrotondando in eccesso)
cleaners_premium = math.ceil(num_premium / 3)
cleaners_standard = math.ceil(num_standard / 3)

# Output
print(f"Appartamenti Premium: {num_premium} -> Cleaner necessari: {cleaners_premium}")
print(f"Appartamenti Standard: {num_standard} -> Cleaner necessari: {cleaners_standard}")
