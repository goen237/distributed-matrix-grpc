import socket
import time
import threading
import os
import json

class Controller:
    def __init__(self, worker_address: tuple, interval: int = 3):
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
                    self.rtts.append(rtt)
                    print(f"Antwort von Worker {address}:{port} erhalten: OK")
                    print(f"Round-Trip-Time: {rtt:.2f} ms\n")
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
    base_name = "worker"  # Name des Workers
    worker_addresses = []

    # Erstellen der Worker-Adressen
    for i in range(1, num_workers + 1):
        host = f"{base_name}"  # Alle Worker nutzen denselben Basisnamen im Netzwerk
        port = base_port  # Jeder Worker hat eine eindeutige Portnummer
        worker_addresses.append((host, port))

    # Healthchecks starten
    manager = HealthCheckManager(worker_addresses)
    rtt_data = manager.start_healthchecks()

    # Ergebnisse anzeigen
    for worker, rtts in rtt_data.items():
        print(f"RTTs für Worker {worker}: {rtts}")

    # RTTs in eine JSON-Datei schreiben
    rtt_data_str = {f"{worker[0]}:{worker[1]}": rtts for worker, rtts in rtt_data.items()}
    with open("rtts.json", "w") as file:
        json.dump(rtt_data_str, file, indent=4)

    print("RTTs in rtts.json gespeichert.")
