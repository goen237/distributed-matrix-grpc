import socket
import time
import threading
import os
import json

class Controller:
    def __init__(self, worker_address: tuple, interval: int = 5):
        self.worker_address = worker_address
        self.interval = interval
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.rtts = []  # Round-Trip-Times Liste für die Worker

    def send_healthcheck(self):
        address, port = self.worker_address
        for i in range(5):  # 5 Healthchecks pro Worker
            start_time = time.time()
            print(f"Sende Healthcheck an {address}:{port} ...")

            self.sock.sendto(b'healthcheck', (address, port))

            try:
                data, _ = self.sock.recvfrom(1024)
                end_time = time.time()

                if data.decode() == 'OK':
                    rtt = (end_time - start_time) * 1000  # RTT in Millisekunden
                    rtt = round(rtt, 2)
                    self.rtts.append(rtt)
                    print(f"Antwort von Worker {address}:{port} erhalten: OK")
                    print(f"Round-Trip-Time: {rtt} ms\n")

                    # Ping an den Worker senden und RTT zurückgeben
                    os.system(f"ping -c 1 {address}")
                else:
                    print(f"Unerwartete Antwort von Worker {address}:{port}")

            except socket.timeout:
                print(f"Keine Antwort von Worker {address}:{port} erhalten.\n")
                self.rtts.append(None)

                time.sleep(self.interval)

    def get_rtts(self):
        return self.rtts  # Liefert die Round-Trip-Times Liste zurück

    def close_socket(self):
        self.sock.close()

class HealthCheckManager:
    def __init__(self, worker_addresses: list):
        self.worker_addresses = worker_addresses
        self.threads = []
        self.results_rtts = {}  # Dictionary für die Round-Trip-Times
        self.controllers = []  # Liste aller Controller-Instanzen

    def start_healthchecks(self):
        for worker in self.worker_addresses:
            controller = Controller(worker)
            self.controllers.append(controller)
            thread = threading.Thread(target=controller.send_healthcheck)
            self.threads.append(thread)

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()

        # Round-Trip Times am Ende der Threads sammeln
        for i, controller in enumerate(self.controllers):
            self.results_rtts[self.worker_addresses[i]] = controller.get_rtts()

        # Sockets schließen
        for controller in self.controllers:
            controller.close_socket()

        return self.results_rtts

if __name__ == "__main__":
    num_workers = int(os.getenv("WORKER_COUNT", "1"))
    base_port = int(os.getenv("WORKER_PORT", "12345"))
    base_name = "group_d_2-worker"  # Name des Workers
    worker_addresses = []

    json_file = "/app/data/rtts.json"

    # Erstellen der Worker-Adressen
    for i in range(1, num_workers + 1):
        host = f"{base_name}-{i}"  # Alle Worker nutzen denselben Basisnamen im Netzwerk
        port = base_port  # Jeder Worker hat eine eindeutige Portnummer
        worker_addresses.append((host, port))

    # Healthchecks starten
    manager = HealthCheckManager(worker_addresses)
    rtt_data = manager.start_healthchecks()

    # Ergebnisse anzeigen
    for worker, rtts in rtt_data.items():
        print(f"RTTs für Worker {worker}: {rtts}")

    # Vorhandene Daten aus der JSON-Datei lesen
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Neue Daten hinzufügen
    new_data = {
        "Workers": num_workers,
        "RTTs": []
    }

    for worker, rtts in rtt_data.items():
        key = f"{worker[0]} : {worker[1]}"
        new_data["RTTs"].append({
            "Worker": key,
            "RTT": rtts
        })

    existing_data.append(new_data)

    # Kombinierte Daten in die JSON-Datei schreiben
    with open(json_file, "w") as f:
        json.dump(existing_data, f, indent=4)

    print("RTTs in rtts.json gespeichert.")
    while True:
        running = True
