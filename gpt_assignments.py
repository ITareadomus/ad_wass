import os
import json
import openai
import passwords
import re

# CONFIGURAZIONE API
openai.api_key = os.getenv(passwords.API_KEY)  # oppure: openai.api_key = "your-api-key"

# Percorso della cartella dove si trova questo script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CARICAMENTO DATI
with open(os.path.join(BASE_DIR, "sel_cleaners.json"), "r") as f:
    cleaners_data = json.load(f)

with open(os.path.join(BASE_DIR, "mock_apartments.json"), "r") as f:
    apartments_data = json.load(f)

# FUNZIONE DI PROMPTING GENERICO
def gpt_prompt(role_prompt, task_prompt):
    client = openai.OpenAI(api_key=passwords.API_KEY)
    response = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-1106:personal::BgVX0bZ3",
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": task_prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

def extract_json(text):
    import re
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    text = re.sub(r'//.*', '', text)
    match = re.search(r'(\[.*\])', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        # Fix: sostituisci task_id1, task_id2... con stringhe
        json_str = re.sub(r'(\[)\s*([a-zA-Z_][a-zA-Z0-9_]*)(,|\s|\])', r'\1"\2"\3', json_str)
        json_str = re.sub(r'([,\[])\s*([a-zA-Z_][a-zA-Z0-9_]*)', r'\1"\2"', json_str)
        # Fix: aggiungi virgole tra oggetti se mancano
        json_str = re.sub(r'\}\s*\{', '},\n{', json_str)
        # Fix: chiudi oggetti e array se manca la parentesi
        if json_str.count('{') > json_str.count('}'):
            json_str += '}'
        if json_str.count('[') > json_str.count(']'):
            json_str += ']'
        try:
            return json.loads(json_str)
        except Exception as e:
            print("Errore parsing JSON:", e)
            print("Testo estratto (dopo fix):", json_str)
            raise
    raise ValueError("Nessun JSON valido trovato nella risposta GPT.")

# FASE 1: CREAZIONE PACCHETTI BILANCIATI PER VICINANZA (NO GMAPS)
role_1 = """
Sei un assistente esperto in logistica urbana. Il tuo compito è creare pacchetti di appartamenti da assegnare ai cleaner, raggruppando le attività in modo ottimale per vicinanza e coerenza logistica.

REGOLE FONDAMENTALI:
- SE CI SONO X CLEANER, DEVI CREARE ESATTAMENTE X PACCHETTI, NON UNO DI PIÙ E NON UNO DI MENO.
- Privilegia la separazione tra NORD e SUD rispetto a EST e OVEST.
- Ogni pacchetto deve contenere SOLO appartamenti dello stesso tipo: STANDARD oppure PREMIUM.
- Ogni pacchetto deve contenere circa 3 appartamenti. Se non è possibile, puoi creare pacchetti da 2 ma mai da 1. Nessun pacchetto può avere più di 4 appartamenti.
- Bilancia il numero di appartamenti nei pacchetti in modo che il carico sia distribuito in modo equo tra i cleaner disponibili.
- Se non è possibile un bilanciamento perfetto, dai priorità alla coerenza geografica.
- Ragiona come se i cleaner dovessero muoversi a piedi o coi mezzi in città. Se due indirizzi ti sembrano appartenere a quartieri diversi o troppo distanti, NON metterli nello stesso pacchetto.

REGOLE DI FORMATO:
- Rispondi SOLO con un JSON valido, senza testo aggiuntivo, senza commenti, senza markdown, senza spiegazioni.
- Ogni oggetto deve essere separato da una virgola.
- Ogni oggetto DEVE essere chiuso correttamente con una parentesi graffa }.
- L'array DEVE essere chiuso con una parentesi quadra ].
- NON lasciare mai una virgola finale dopo l'ultimo oggetto.
- NON usare mai commenti o testo fuori dal JSON.
- NON usare markdown (niente ``` o simili).
- NON aggiungere nessuna spiegazione prima o dopo il JSON.
- Se il JSON non è valido, correggilo e rispondi solo con il JSON valido.

Esempio di formato richiesto:
[
  {
    "package_id": "pkg_1",
    "type": "STANDARD",
    "tasks": ["100001", "100002", "100003"]
  },
  {
    "package_id": "pkg_2",
    "type": "PREMIUM",
    "tasks": ["100004", "100005", "100006"]
  }
]
"""


task_1 = f"""
Ecco la lista degli appartamenti:
{json.dumps(apartments_data['apt'], indent=2)}

ATTENZIONE: Appartamenti come "Via Tortona, 27" e "Via Lambrate, 20" sono **molto lontani** tra loro e **non devono mai essere nello stesso pacchetto**.
Allo stesso modo, raggruppa sempre insieme appartamenti che si trovano **nel centro storico** o **nella stessa area geografica**.


Raggruppa gli appartamenti in pacchetti come specificato. Restituisci un JSON così strutturato:
Rispondi SOLO con il JSON richiesto. NESSUNA PAROLA IN PIU perchè devo passarlo a un sistema che lo interpreta automaticamente. (Assicurati che il JSON sia valido e che ogni oggetto sia separato da una virgola.)
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
print("GPT OUTPUT:\n", clusters_output)
clusters = extract_json(clusters_output)



# FASE 2: ORDINAMENTO INTERNO DI OGNI PACCHETTO
role_2 = """
Sei un assistente logistico specializzato nella pianificazione delle pulizie. Devi ordinare gli appartamenti all'interno di ogni pacchetto.

REGOLE DI FORMATO:
- Rispondi SOLO con un JSON valido, senza testo aggiuntivo, senza commenti, senza markdown, senza spiegazioni.
- La lista deve essere una lista di stringhe, ogni task_id tra virgolette doppie, ad esempio: ["100001", "100002", "100003"]
- NON usare mai variabili come task_id1, task_id2, ma solo i veri task_id.
- NON lasciare mai una virgola finale dopo l'ultimo elemento.
- NON usare mai commenti o testo fuori dal JSON.
- NON usare markdown (niente ``` o simili).
- NON aggiungere nessuna spiegazione prima o dopo il JSON.
- Se il JSON non è valido, correggilo e rispondi solo con il JSON valido.
"""

ordered_clusters = []
for cluster in clusters:
    task_ids = cluster['tasks']
    tasks_full = [apt for apt in apartments_data['apt'] if apt['task_id'] in task_ids]
    task_2 = f"""
Ecco il pacchetto da ordinare:
{json.dumps(tasks_full, indent=2)}

Restituisci la lista ordinata solo con i task_id: (Assicurati che il JSON sia valido e che ogni oggetto sia separato da una virgola.)
(Rispondi solo con il JSON richiesto, senza alcun testo aggiuntivo.)
[task_id1, task_id2, ...]
"""
    gpt_response = gpt_prompt(role_2, task_2)
    print("DEBUG GPT response (fase 2):", repr(gpt_response))
    ordered_task_ids = extract_json(gpt_response)
    cluster['tasks'] = ordered_task_ids
    ordered_clusters.append(cluster)

# FASE 3: ASSEGNAZIONE AI CLEANER
role_3 = """
Sei un assistente HR. Devi assegnare i pacchetti ai cleaner disponibili in modo bilanciato.
Ogni cleaner ha un contratto:
- A: 20h/settimana
- B: 30h/settimana
- C: 40h/settimana

Ogni cleaner ha un counter_hours (ore già lavorate). Assegna i pacchetti ai cleaner compatibili per tipo (STANDARD o PREMIUM).
Cerca di:
- Bilanciare le ore totali
- Assegnare i pacchetti più lunghi ai cleaner a cui mancano ore per raggiungere il minimo del contratto

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
assignments = extract_json(assignments_output)

# SALVA RISULTATO
with open("final_assignments.json", "w") as f:
    json.dump(assignments, f, indent=2)

print("Assegnazioni completate e salvate.")

# REPORT DETTAGLIATO
task_map = {a['task_id']: a for a in apartments_data['apt']}
cleaner_map = {c['id']: f"{c['name']} {c['lastname']} ({c['role']})" for c in cleaners_data['cleaners']}

with open("report.txt", "w", encoding="utf-8") as f:
    for a in assignments:
        cid = a['cleaner_id']
        cleaner_name = cleaner_map.get(cid, f"ID {cid}")
        f.write(f"Cleaner: {cleaner_name}\n")
        total_minutes = a.get("total_assigned_minutes", 0)
        total_hours = round(total_minutes / 60, 2)
        for idx, tid in enumerate(a.get("assigned_tasks", [])):
            t = task_map.get(tid, {})
            address = t.get('address', '')
            checkin = t.get('checkin_time', '')
            checkout = t.get('checkout_time', '')
            distanza = t.get('distanza', '')
            durata = t.get('durata', '')
            f.write(f"  {idx+1}. Task {tid}: {address} - checkin: {checkin} | checkout: {checkout}\n")
            if distanza or durata:
                f.write(f"     -> distanza: {distanza}, durata: {durata}\n")
        f.write(f"\n  ➤ Totale ore assegnate: {total_hours}\n\n")

print("report.txt generato.")
