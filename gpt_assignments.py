import json
import openai
import os
import passwords
import re

# CONFIGURAZIONE API
openai.api_key = os.getenv(passwords.API_KEY)  # oppure: openai.api_key = "your-api-key"

# CARICAMENTO DATI
with open("sel_cleaners.json", "r") as f:
    cleaners_data = json.load(f)

with open("mock_apartments.json", "r") as f:
    apartments_data = json.load(f)

# FUNZIONE DI PROMPTING GENERICO
def gpt_prompt(role_prompt, task_prompt):
    client = openai.OpenAI(api_key=passwords.API_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": task_prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

def extract_json(text):
    # Rimuovi blocchi di codice markdown e spazi inutili
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    # Rimuovi i commenti // ... (solo su linee singole)
    text = re.sub(r'//.*', '', text)
    match = re.search(r'(\[.*\])', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except Exception as e:
            print("Errore parsing JSON:", e)
            print("Testo estratto:", json_str)
            raise
    raise ValueError("Nessun JSON valido trovato nella risposta GPT.")

# FASE 1: CREAZIONE PACCHETTI BILANCIATI PER VICINANZA (NO GMAPS)
role_1 = """
Sei un assistente esperto in logistica urbana. Il tuo compito è creare pacchetti di appartamenti da assegnare ai cleaner, raggruppando le attività in modo ottimale per vicinanza e coerenza logistica.

REGOLE PER LA CREAZIONE DEI PACCHETTI:
REGOLA SACRA: SE CI SONO X CLEANER, DEVI CREARE ESATTAMENTE X PACCHETTI, NON UNO DI PIU' E NON UNO DI MENO.
ALTRA REGOLA SACRA:  Privilegia la separazione tra NORD e SUD rispetto che a EST e OVEST MIRACCOMANDO ASSOLUTMANETE IMPORTANTISSIMO.

1. **Vicinanza geografica**:
   - Ogni pacchetto deve contenere appartamenti **molto vicini tra loro**.
   - Considera vicine vie che sembrano appartenere alla **stessa zona urbana** o quartiere.
   - Evita assolutamente di accorpare vie che appaiono in **quartieri opposti** o distanti.

2. **Tipologia coerente**:
   - Ogni pacchetto deve contenere solo appartamenti dello **stesso tipo**: `STANDARD` oppure `PREMIUM`.

3. **Numero di appartamenti per pacchetto**:
   - Ogni pacchetto deve contenere **circa 3 appartamenti**.
   - Se non è possibile, puoi creare pacchetti da **2** ma **mai da 1**.
   - ATTENZIONE: **ogni cleaner deve ricevere ESATTAMENTE pacchetto con almeno 2 appartamenti, e non più di 4**.

4. **Bilanciamento dei pacchetti**:
   - Bilancia il numero di apt. nei pacchetti in modo che il carico sia distribuito in modo equo tra i cleaner disponibili. Dev'essere esattamente UN pacchetto PER ogni cleaner, quindi non fare più pacchetti del num. di cleaner disponibili.
   - Se non è possibile un bilanciamento perfetto, dai **priorità alla coerenza geografica** piuttosto che alla distribuzione uniforme.

5. **Formato del risultato**:
   - Restituisci un JSON con una lista di pacchetti, ognuno nel formato:
     {
       "package_id": "pkg_1",
       "type": "STANDARD" o "PREMIUM",
       "tasks": [<lista_di_task_id>]
     }

 Ragiona come se i cleaner dovessero fare il giro a piedi o coi mezzi in città. Se due indirizzi ti sembrano appartenere a quartieri diversi o troppo distanti, **non metterli nello stesso pacchetto**.

Rispondi SOLO con il JSON richiesto. NESSUNA PAROLA IN PIU perchè devo passarlo a un sistema che lo interpreta automaticamente.
"""


task_1 = f"""
Ecco la lista degli appartamenti:
{json.dumps(apartments_data['apt'], indent=2)}

ATTENZIONE: Appartamenti come "Via Tortona, 27" e "Via Lambrate, 20" sono **molto lontani** tra loro e **non devono mai essere nello stesso pacchetto**.
Allo stesso modo, raggruppa sempre insieme appartamenti che si trovano **nel centro storico** o **nella stessa area geografica**.


Raggruppa gli appartamenti in pacchetti come specificato. Restituisci un JSON così strutturato:
Rispondi SOLO con il JSON richiesto. NESSUNA PAROLA IN PIU perchè devo passarlo a un sistema che lo interpreta automaticamente.
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
Regole da seguire:
- Inizia a pulire non prima del checkout_time
- Finisci prima del checkin_time
- Se un appartamento ha small_equipment = true, cerca di farlo all'inizio del giro del pacchetto
- Minimizza i tempi di spostamento
"""

ordered_clusters = []
for cluster in clusters:
    task_ids = cluster['tasks']
    tasks_full = [apt for apt in apartments_data['apt'] if apt['task_id'] in task_ids]
    task_2 = f"""
Ecco il pacchetto da ordinare:
{json.dumps(tasks_full, indent=2)}

Restituisci la lista ordinata solo con i task_id:
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
