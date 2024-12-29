# import json
# import os
# import matplotlib.pyplot as plt

# # JSON-Datei mit den RTT-Daten
# json_file = "rtts.json"

# # Vorhandene Daten aus der JSON-Datei lesen
# if os.path.exists(json_file):
#     with open(json_file, "r") as f:
#         data = json.load(f)
# else:
#     data = []

# # Durchschnittliche RTT-Zeiten je nach Anzahl von Workern berechnen
# worker_counts = []
# average_rtts = []

# for entry in data:
#     worker_count = entry["Workers"]
#     rtts = [rtt for worker in entry["RTTs"] for rtt in worker["RTT"] if rtt is not None]
#     if rtts:
#         average_rtt = sum(rtts) / len(rtts)
#     else:
#         average_rtt = 0
#     worker_counts.append(worker_count)
#     average_rtts.append(average_rtt)

# # Diagramm erstellen
# plt.figure(figsize=(10, 6))
# plt.plot(worker_counts, average_rtts, marker='o')
# plt.xlabel('Anzahl von Workern')
# plt.ylabel('Durchschnittliche RTT-Zeit (ms)')
# plt.title('Durchschnittliche RTT-Zeit (ms) je nach Anzahl von Workern')
# plt.grid(True)
# plt.show()


import os
import json
import numpy as np
import matplotlib.pyplot as plt

# JSON-Datei mit den RTT-Daten
json_file = "data/rtt_data.json"

# Vorhandene Daten aus der JSON-Datei lesen
if os.path.exists(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
else:
    data = []

# RTT-Werte extrahieren
all_rtt_values = []
# Statistik für jeden Worker berechnen
worker_statistics = {}
for idx, entry in enumerate(data):
    worker_name = entry.get("Worker", f"Worker_{idx + 1}")
    rtt_values = entry.get("RTT", [])
    all_rtt_values.extend(rtt_values)

    if rtt_values:
        worker_statistics[worker_name] = {
            "mean": np.mean(rtt_values),
            "median": np.median(rtt_values),
            "min": np.min(rtt_values),
            "max": np.max(rtt_values),
            "std_dev": np.std(rtt_values)
        }
    else:
        worker_statistics[worker_name] = None

# Gesamte Statistik berechnen
total_statistics = {
    "mean": np.mean(all_rtt_values),
    "median": np.median(all_rtt_values),
    "min": np.min(all_rtt_values),
    "max": np.max(all_rtt_values),
    "std_dev": np.std(all_rtt_values)
}

# Statistik ausgeben
print("Gesamte RTT-Statistik:")
for key, value in total_statistics.items():
    print(f"{key.capitalize()}: {value:.2f} ms")

print("\nStatistik für jeden Worker:")
for worker, stats in worker_statistics.items():
    if stats:
        print(f"\n{worker}:")
        for key, value in stats.items():
            print(f"  {key.capitalize()}: {value:.2f} ms")
    else:
        print(f"\n{worker}: Keine RTT-Daten verfügbar.")

# Diagramm erstellen
fig, ax = plt.subplots(figsize=(10, 6))
for idx, entry in enumerate(data):
    worker_name = entry.get("Worker", f"Worker_{idx + 1}")
    rtt_values = entry.get("RTT", [])
    ax.plot(rtt_values, label=worker_name)

ax.set_title("RTT-Werte pro Worker")
ax.set_xlabel("RTT-Messpunkt")
ax.set_ylabel("RTT (ms)")
ax.legend(loc='upper right')
ax.grid(True)

# Diagramm speichern und anzeigen
plt.tight_layout()
plt.savefig("rtt_statistik.png")
plt.show()