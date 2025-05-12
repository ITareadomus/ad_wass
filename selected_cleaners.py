'''import json
import math

# === Carica cleaners e appartamenti ===
with open("mock_cleaners.json", "r") as f:
    all_data = json.load(f)

cleaners = all_data.get("cleaners", [])

with open("mock_apartments.json", "r") as f:
    apt_data = json.load(f)

apartments = apt_data.get("apt", [])

# === Conta appartamenti per tipo ===
premium_apts = [apt for apt in apartments if apt.get("type") == "Premium"]
standard_apts = [apt for apt in apartments if apt.get("type") == "Standard"]

# Cleaner richiesti
num_premium_cleaners = math.ceil(len(premium_apts) / 3)
num_standard_cleaners = math.ceil(len(standard_apts) / 3)

# === Filtra cleaner validi ===
valid_cleaners = [
    cleaner for cleaner in cleaners
    if cleaner.get("active") is True
    and cleaner.get("available") is True
]

# === Seleziona cleaner ===
def select_cleaners(role, num_needed):
    # Filtra per ruolo
    filtered = [c for c in valid_cleaners if c.get("role") == role]

    # Ordina per ranking decrescente e counter_hours crescente
    sorted_cleaners = sorted(
        filtered,
        key=lambda c: (-c.get("ranking", 0), c.get("counter_hours", 0))
    )

    # Priorità a cleaner con counter_days <= 6
    priority_cleaners = [c for c in sorted_cleaners if c.get("counter_days", 0) <= 6]
    backup_cleaners = [c for c in sorted_cleaners if 6 < c.get("counter_days", 0) <= 12]

    # Combina le due liste, dando priorità ai cleaner con meno giorni consecutivi lavorati
    final_cleaners = priority_cleaners + backup_cleaners

    # Seleziona il numero richiesto di cleaner
    return final_cleaners[:num_needed]

# Seleziona cleaner Premium e Standard
selected_premium = select_cleaners("Premium", num_premium_cleaners)
selected_standard = select_cleaners("Standard", num_standard_cleaners)

selected_cleaners = selected_premium + selected_standard

# === Salva in JSON ===
with open("selected_cleaners.json", "w") as f:
    json.dump({"selected_cleaners": selected_cleaners}, f, indent=4)

# Output di riepilogo
print(f"Cleaner Premium richiesti: {num_premium_cleaners}, selezionati: {len(selected_premium)}")
print(f"Cleaner Standard richiesti: {num_standard_cleaners}, selezionati: {len(selected_standard)}")
print(f"Totale cleaner selezionati: {len(selected_cleaners)}")
'''