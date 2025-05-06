import subprocess
import json
import math
from gmaps import calcola_distanza


def run_dependency_scripts():
    subprocess.run(["python3", "cleaner_list.py"])
    subprocess.run(["python3", "task_selection.py"])


def load_data():
    with open("modello_cleaners.json") as f:
        cleaners = json.load(f)
    with open("modello_apt.json") as f:
        apartments = json.load(f)
    return cleaners, apartments


def calculate_cleaners_needed(apartments):
    premium = [a for a in apartments if a["type"] == "premium"]
    standard = [a for a in apartments if a["type"] == "standard"]
    needed_premium = math.ceil(len(premium) / 3.5)
    needed_standard = math.ceil(len(standard) / 3.5)
    return needed_premium, needed_standard


def filter_priority1_apts(apartments):
    return [a for a in apartments if a["checkin_time"] == "14:00" or a["dotazione"] == "piccola"]


def assign_priority(cleaners, apartments, priority_level, previous_assignments):
    assignments = []
    for cleaner in cleaners:
        suitable_apts = [a for a in apartments if
                         a["type"] == cleaner["role"] and
                         a["id"] not in [x["apt_id"] for x in previous_assignments]]
        if suitable_apts:
            apt = suitable_apts.pop(0)
            assignments.append({
                "cleaner_id": cleaner["id"],
                "apt_id": apt["id"],
                "priority": priority_level,
                "start_time": "08:00",  # iniziale dummy
                "estimated_end": "09:00"  # dummy
            })
    return assignments


def find_closest_apt(cleaner_last_apt, remaining_apts):
    distances = []
    for apt in remaining_apts:
        distance = calcola_distanza(
            cleaner_last_apt["lat"], cleaner_last_apt["lng"],
            apt["lat"], apt["lng"]
        )
        distances.append((apt, distance))
    distances.sort(key=lambda x: x[1])
    return distances[0][0] if distances else None


def assign_by_distance(cleaners, apartments, current_priority, existing_assignments):
    new_assignments = []
    for cleaner in cleaners:
        last_assignment = max(
            [a for a in existing_assignments if a["cleaner_id"] == cleaner["id"]],
            key=lambda x: x["priority"],
            default=None
        )
        if last_assignment:
            last_apt = next(a for a in apartments if a["id"] == last_assignment["apt_id"])
            remaining_apts = [a for a in apartments if
                              a["type"] == cleaner["role"] and
                              a["id"] not in [x["apt_id"] for x in existing_assignments]]
            next_apt = find_closest_apt(last_apt, remaining_apts)
            if next_apt:
                new_assignments.append({
                    "cleaner_id": cleaner["id"],
                    "apt_id": next_apt["id"],
                    "priority": current_priority
                })
    return new_assignments


def save_assignments(assignments):
    with open("assignments.json", "w") as f:
        json.dump(assignments, f, indent=4)


def main():
    run_dependency_scripts()
    cleaners, apartments = load_data()

    n_premium, n_standard = calculate_cleaners_needed(apartments)
    premium_cleaners = [c for c in cleaners if c["role"] == "premium"][:n_premium]
    standard_cleaners = [c for c in cleaners if c["role"] == "standard"][:n_standard]

    priority1_apts = filter_priority1_apts(apartments)
    assignments = assign_priority(premium_cleaners + standard_cleaners, priority1_apts, 1, [])

    assignments += assign_by_distance(premium_cleaners + standard_cleaners, apartments, 2, assignments)
    assignments += assign_by_distance(premium_cleaners + standard_cleaners, apartments, 3, assignments)

    save_assignments(assignments)


if __name__ == "__main__":
    main()
