import json
import openai
import os

# CONFIGURAZIONE API
openai.api_key = os.getenv("OPENAI_API_KEY")  # O inserisci direttamente: openai.api_key = "your-api-key"

# CARICAMENTO DATI
with open("cleaners.json", "r") as f:
    cleaners_data = json.load(f)

with open("apartments.json", "r") as f:
    apartments_data = json.load(f)

# FUNZIONE DI PROMPTING GENERICO
def gpt_prompt(role_prompt, task_prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # o "gpt-4-1106-preview" se vuoi un modello più recente
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": task_prompt}
        ],
        temperature=0.7,
    )
    return response['choices'][0]['message']['content']

# FASE 1: RAGGRUPPAMENTO APPARTAMENTI VICINI
role_1 = "Sei un assistente esperto in ottimizzazione logistica urbana. Raggruppa gli appartamenti più vicini per minimizzare gli spostamenti a piedi o coi mezzi pubblici."
task_1 = f"""Ecco i dati degli appartamenti da pulire oggi:
{json.dumps(apartments_data['apartments'], indent=2)}
Raggruppali in pacchetti da assegnare ai cleaner in base alla distanza (lat, lng). Restituisci una lista di pacchetti in formato JSON, ciascuno con un elenco ordinato di appartamenti (per ora solo raggruppati per prossimità).
"""

clusters_output = gpt_prompt(role_1, task_1)
clusters = json.loads(clusters_output)

# FASE 2: ORDINAMENTO DEI TASK PER PACCHETTO
role_2 = "Sei un assistente logistico esperto in pianificazione delle pulizie. Devi ordinare gli appartamenti in ogni pacchetto basandoti su checkout e checkin e assegnare priorità a quelli con small_equipment true."
ordered_clusters = []

for cluster in clusters:
    task_2 = f"""Ecco un pacchetto di appartamenti: {json.dumps(cluster, indent=2)}.
Ordinami l’elenco rispettando:
- Non iniziare prima del checkout_time
- Finire prima del checkin_time
- Inizia da quelli con small_equipment = true
- Minimizza i tempi di spostamento tra un apt e il successivo
Restituisci il pacchetto ordinato come lista JSON degli appartamenti.
"""
    ordered_cluster = gpt_prompt(role_2, task_2)
    ordered_clusters.append(json.loads(ordered_cluster))

# FASE 3: ASSEGNAZIONE AI CLEANER BASATA SU CONTRATTO E ORE LAVORATE
role_3 = "Sei un assistente HR e logistico. Ogni pacchetto di pulizie va assegnato a un cleaner disponibile cercando di bilanciare il totale delle ore mensili in base al contratto: A (20h), B (30h), C (40h). Considera counter_hours."
task_3 = f"""Ecco i cleaner disponibili:
{json.dumps(cleaners_data['cleaners'], indent=2)}
Ecco i pacchetti di appartamenti ordinati con cleaning_time in minuti:
{json.dumps(ordered_clusters, indent=2)}
Assegna ogni pacchetto a un cleaner. Restituisci una lista JSON con:
[
  {{
    "cleaner_id": 18,
    "assigned_tasks": [...],
    "total_assigned_minutes": 240
  }},
  ...
]
"""

assignments_output = gpt_prompt(role_3, task_3)
assignments = json.loads(assignments_output)

# SALVA RISULTATO
with open("final_assignments.json", "w") as f:
    json.dump(assignments, f, indent=2)

print("Assegnazioni completate e salvate.")

# --- SALVA REPORT GPT SIMILE AD ALGORITMO.PY ---
# Carica di nuovo i dati degli appartamenti per mappare task_id → info
with open("apartments.json", "r") as f:
    apartments_data = json.load(f)
apt_map = {a['task_id']: a for a in apartments_data.get('apartments', [])}

with open("gpt_report.txt", "w", encoding="utf-8") as f:
    for asg in assignments:
        cleaner_id = asg.get("cleaner_id")
        f.write(f"Cleaner ID: {cleaner_id}\n")
        assigned_tasks = asg.get("assigned_tasks", [])
        for idx, tid in enumerate(assigned_tasks):
            apt = apt_map.get(tid, {})
            f.write(f"  {idx+1}. Task {tid}: {apt.get('address','')} - checkin: {apt.get('checkin','')} {apt.get('checkin_time','')} | checkout: {apt.get('checkout','')} {apt.get('checkout_time','')}\n")
            # opzionale: puoi aggiungere distanza/durata se vuoi calcolarla qui
        f.write(f"\n  ➤ Totale minuti assegnati: {asg.get('total_assigned_minutes', 0)}\n\n")

print("gpt_report.txt generato.")
