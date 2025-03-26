import random
import googlemaps
from collections import defaultdict
from utils.openai_prompting import generate_prompt, get_openai_response

gmaps = googlemaps.Client(key="YOUR_GOOGLE_MAPS_API_KEY")

def generate_mock_data():
    cleaners = [
        {"id": i, "name": f"Cleaner_{i}", "type": "Premium" if i % 2 == 0 else "Standard", "location": (random.randint(0, 100), random.randint(0, 100))}
        for i in range(1, 21)
    ]
    
    apartments = [
        {"id": i, "priority": random.randint(1, 5), "type": "Premium" if i % 2 == 0 else "Standard", 
         "location": (random.randint(0, 100), random.randint(0, 100)), "time": random.uniform(1, 3)}
        for i in range(101, 201)
    ]
    return cleaners, apartments

def sort_by_priority(apartments):
    return sorted(apartments, key=lambda x: x["priority"], reverse=True)

def filter_by_type(items, type_value):
    return [item for item in items if item["type"] == type_value]

def get_distance(loc1, loc2):
    result = gmaps.distance_matrix(loc1, loc2, mode="driving")
    return result["rows"][0]["elements"][0]["distance"]["value"] if result["rows"][0]["elements"][0]["status"] == "OK" else float("inf")

def find_best_next_apartment(cleaner, available_apts, current_apt):
    if not available_apts:
        return None
    
    available_apts = [apt for apt in available_apts if apt["type"] == cleaner["type"] or cleaner["type"] == "Premium"]
    if not available_apts:
        return None
    
    return min(available_apts, key=lambda apt: get_distance(current_apt["location"], apt["location"]))

def assign_apartments(apartments, cleaners):
    assignments = defaultdict(list)
    
    for apt in apartments:
        available_cleaners = [c for c in cleaners if c["type"] == apt["type"] or c["type"] == "Premium"]
        if not available_cleaners:
            continue
        
        cleaner = min(available_cleaners, key=lambda c: (len(assignments[c["name"]]), get_distance(c["location"], apt["location"])))
        assignments[cleaner["name"]].append(apt)
    
    remaining_apartments = [apt for apt in apartments if apt not in sum(assignments.values(), [])]
    for cleaner in cleaners:
        if cleaner["name"] in assignments and assignments[cleaner["name"]]:
            first_apt = assignments[cleaner["name"]][0]
            next_apt = find_best_next_apartment(cleaner, remaining_apartments, first_apt)
            if next_apt:
                assignments[cleaner["name"]].append(next_apt)
                remaining_apartments.remove(next_apt)
    
    return assignments

def main():
    cleaners, apartments = generate_mock_data()
    
    apartments_premium = sort_by_priority(filter_by_type(apartments, "Premium"))
    apartments_standard = sort_by_priority(filter_by_type(apartments, "Standard"))
    
    cleaners_premium = filter_by_type(cleaners, "Premium")
    cleaners_standard = filter_by_type(cleaners, "Standard")
    
    assignments_premium = assign_apartments(apartments_premium, cleaners_premium)
    assignments_standard = assign_apartments(apartments_standard, cleaners_standard)
    
    print("Assegnazioni Premium:")
    for cleaner, apts in assignments_premium.items():
        print(f"{cleaner}: {[apt['id'] for apt in apts]}")
    
    print("\nAssegnazioni Standard:")
    for cleaner, apts in assignments_standard.items():
        print(f"{cleaner}: {[apt['id'] for apt in apts]}")

if __name__ == "__main__":
    main()
