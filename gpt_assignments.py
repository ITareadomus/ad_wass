import json
import pandas as pd
from sklearn.cluster import KMeans
from geopy.distance import geodesic

# === CONFIG ===
OUTPUT_FILE = "assegnazioni_gpt.txt"

# === Load Data ===
with open("mock_apartments.json") as f:
    apartments_data = json.load(f)["apt"]

with open("sel_cleaners.json") as f:
    cleaners_data = json.load(f)

cleaners = cleaners_data["cleaners"][:4]

# === Preprocess Apartments ===
apartments_df = pd.DataFrame(apartments_data)
apartments_df["lat"] = apartments_df["lat"].astype(float)
apartments_df["lng"] = apartments_df["lng"].astype(float)

# === KMeans Clustering ===
kmeans = KMeans(n_clusters=4, random_state=42)
apartments_df["cluster"] = kmeans.fit_predict(apartments_df[["lat", "lng"]])

# === Cleaner Setup ===
assignments = {cleaner["id"]: [] for cleaner in cleaners}

# === Assign clusters to cleaners ===
cluster_groups = apartments_df.groupby("cluster")
sorted_clusters = sorted(cluster_groups, key=lambda x: len(x[1]), reverse=True)

for i, (cluster_id, group) in enumerate(sorted_clusters):
    cleaner_id = cleaners[i % 4]["id"]
    assignments[cleaner_id] = group.copy()

# === Sort apartments within each cluster by distance ===
def sort_by_distance(group_df):
    coords = list(zip(group_df["lat"], group_df["lng"]))
    if not coords:
        return group_df
    start = coords[0]
    sorted_indices = []
    visited = set()

    while len(visited) < len(coords):
        min_dist = float("inf")
        next_idx = None
        for idx, coord in enumerate(coords):
            if idx in visited:
                continue
            dist = geodesic(start, coord).meters
            if dist < min_dist:
                min_dist = dist
                next_idx = idx
        visited.add(next_idx)
        sorted_indices.append(next_idx)
        start = coords[next_idx]

    return group_df.iloc[sorted_indices]

# === Write output ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as out_file:
    for cleaner in cleaners:
        cleaner_id = cleaner["id"]
        cleaner_name = cleaner.get("name", f"Cleaner {cleaner_id}")
        out_file.write(f"Cleaner: {cleaner_name} (Standard)\n")
        
        tasks = sort_by_distance(assignments[cleaner_id])
        total_minutes = 0
        previous = None
        
        for i, task in enumerate(tasks.itertuples(), start=1):
            line = f"  {i}. Task {task.task_id}: {task.address} - checkin: {task.checkin} {task.checkin_time} | checkout: {task.checkout} {task.checkout_time}\n"
            out_file.write(line)
            
            if previous:
                dist = geodesic((previous.lat, previous.lng), (task.lat, task.lng)).meters
                time_min = dist / 1000 * 8  # approx 8 min/km walking
                total_minutes += time_min
                detail = f"     -> distanza: {int(dist)}m, durata: {round(time_min, 1)} min\n"
                out_file.write(detail)
            previous = task
        
        total_hours = (len(tasks) * 60 + total_minutes) / 60
        out_file.write(f"\n  ➤ Totale ore assegnate: {round(total_hours, 2)}\n\n")

print(f"✅ Assegnazioni salvate in '{OUTPUT_FILE}'")


