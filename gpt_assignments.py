import json
import openai
import os

# CONFIGURAZIONE API
openai.api_key = os.getenv("OPENAI_API_KEY")  # oppure: openai.api_key = "your-api-key"

# CARICAMENTO DATI
with open("cleaners.json", "r") as f:
    cleaners_data = json.load(f)

with open("apartments.json", "r") as f:
    apartments_data = json.load(f)

# FUNZIONE DI PROMPTING GENERICO
def gpt_prompt(role_prompt, task_prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": task_prompt}
        ],
        temperature=0.7,
    )
    return response['choices'][0]['message']['content']

# FASE 1: CREAZIONE PACCHETTI BILANCIATI PER VICINANZA (NO GMAPS)
role_1 = """
Sei un assistente esperto in logistica urbana. Il tuo compito è raggruppare gli appartamenti in pacchetti da assegnare ai cleaner. 
Ogni pacchetto deve contenere appartamenti vicini tra loro e tutti dello stesso tipo (STANDARD o PREMIUM).
Ogni pacchetto deve contenere al massimo 3-4 appartamenti, bilanciando il numero di task. Ignora qualsiasi vincolo sui km o durata.
"""

task_1 = f"""
Ecco la lista degli appartamenti:
{json.dumps(apartments_data['apartments'], indent=2)}

Raggruppa gli appartamenti in pacchetti come specificato. Restituisci un JSON così strutturato:
[
  {{
    "package_id": "pkg_1",
    "type": "STANDARD",
    "tasks": [<lista_di_task_id>]
  }},
  ...
]
"""

clusters_output = gpt_prompt(role_1, task_1)
clusters = json.loads(clusters_output)

# FASE 2: ORDINAMENTO INTERNO DI OGNI PACCHETTO
role_2 = """
Sei un assistente logistico specializzato nella pianificazione delle pulizie. Devi ordinare gli appartamenti all'interno di ogni pacchetto.
Regole da seguire:
- Inizia a pulire circa 30 minuti dopo il checkout_time
- Finisci prima del checkin_time
- Se un appartamento ha small_equipment = true, considera se è il caso di farlo all'inizio
- Minimizza i tempi di spostamento
"""

ordered_clusters = []
for cluster in clusters:
    task_ids = cluster['tasks']
    tasks_full = [apt for apt in apartments_data['apartments'] if apt['task_id'] in task_ids]
    task_2 = f"""
Ecco il pacchetto da ordinare:
{json.dumps(tasks_full, indent=2)}

Restituisci la lista ordinata solo con i task_id:
[task_id1, task_id2, ...]
"""
    ordered_task_ids = json.loads(gpt_prompt(role_2, task_2))
    cluster['tasks'] = ordered_task_ids
    ordered_clusters.append(cluster)

# FASE 3: ASSEGNAZIONE AI CLEANER
role_3 = """
Sei un assistente HR. Devi assegnare i pacchetti ai cleaner disponibili in modo bilanciato.
Ogni cleaner ha un contratto:
- A: 20h/mese
- B: 30h/mese
- C: 40h/mese

Ogni cleaner ha un counter_hours (ore già lavorate). Assegna i pacchetti ai cleaner compatibili per tipo (STANDARD o PREMIUM).
Cerca di:
- Bilanciare le ore totali
- Preferire cleaner con ranking alto per task più lunghi

Restituisci un JSON come questo:
[
  {{
    "cleaner_id": 42,
    "assigned_tasks": [<lista_task_id>],
    "total_assigned_minutes": 235
  }},
  ...
]
"""

task_3 = f"""
Cleaner disponibili:
{json.dumps(cleaners_data['cleaners'], indent=2)}

Pacchetti disponibili:
{json.dumps(ordered_clusters, indent=2)}
"""

assignments_output = gpt_prompt(role_3, task_3)
assignments = json.loads(assignments_output)

# SALVA RISULTATO
with open("final_assignments.json", "w") as f:
    json.dump(assignments, f, indent=2)

print("Assegnazioni completate e salvate.")

# REPORT DETTAGLIATO
task_map = {a['task_id']: a for a in apartments_data['apartments']}

with open("gpt_report.txt", "w", encoding="utf-8") as f:
    for a in assignments:
        cid = a['cleaner_id']
        f.write(f"Cleaner ID: {cid}\n")
        total = a.get("total_assigned_minutes", 0)
        for idx, tid in enumerate(a.get("assigned_tasks", [])):
            t = task_map.get(tid, {})
            f.write(f"  {idx+1}. Task {tid}: {t.get('address','')} - checkin: {t.get('checkin_time','')} | checkout: {t.get('checkout_time','')}\n")
        f.write(f"  ➤ Totale minuti assegnati: {total}\n\n")

print("gpt_report.txt generato.")
