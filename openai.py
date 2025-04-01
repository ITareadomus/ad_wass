import openai

def generate_prompt(assignments):
    prompt = """
    Sei un assistente esperto nell'ottimizzazione delle assegnazioni degli appartamenti ai cleaner.
    Ti fornisco le attuali assegnazioni e devi suggerire miglioramenti in base a:
    - Distanza tra gli appartamenti
    - Tempo di pulizia previsto
    - Bilanciamento del carico di lavoro tra i cleaner
    
    Ecco le assegnazioni attuali:
    """
    
    for cleaner, apts in assignments.items():
        apt_list = ", ".join([f"APT-{apt['id']} (Priorità {apt['priority']}, Tempo {apt['time']}h)" for apt in apts])
        prompt += f"{cleaner}: {apt_list}\n"
    
    prompt += "\nSuggerisci eventuali riassegnazioni per migliorare l'efficienza."
    return prompt

def get_optimized_assignments(assignments):
    prompt = generate_prompt(assignments)
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Sei un esperto di logistica delle pulizie."},
                  {"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response["choices"][0]["message"]["content"]

if __name__ == "__main__":
    mock_assignments = {
        "Cleaner_1": [{"id": 101, "priority": 5, "time": 2.5}, {"id": 105, "priority": 3, "time": 1.8}],
        "Cleaner_2": [{"id": 102, "priority": 4, "time": 2.0}]
    }
    print(get_optimized_assignments(mock_assignments))