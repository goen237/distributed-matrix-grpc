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
        self.rtts = [] # Round-Trip-Times Liste für die Worker

    def send_healthcheck(self):
        address, port = self.worker_address
        i = 0
        while i < 5: # 5 Healthchecks pro Worker
            start_time = time.time()
            print(f"Sende Healthcheck an {address} : {port} ...")

            self.sock.sendto(b'healthcheck', (address, port))

            try:
                data, _ = self.sock.recvfrom(1024)
                end_time = time.time()

                if data.decode() == 'OK':
                    rtt = (end_time - start_time) * 1000  # RTT in millisecondes

                    self.rtts.append(rtt)
                    print(f"Antwort von Worker {address} -> {port} erhalten: OK")
                    print(f"\nRound-Trip-Time {address}: {rtt:.2f} ms\n")

            except socket.timeout:
                print(f"Keine Antwort vom Worker {address} : {port} erhalten.\n")
                self.rtts.append(None)

            i += 1
            time.sleep(self.interval)

        self.sock.sendto(b'stop', (address, port))
        self.sock.close()

    def get_rtts(self):
        return self.rtts # liefert die Round-Trip-Times Liste zurück

class HealthCheckManager:
    def __init__(self, worker_addresses: list):
        self.worker_addresses = worker_addresses
        self.threads = []
        self.results_rtts = {} # Dictionary für die Round-Trip-Times

    def start_healthchecks(self):
        Controllers = []
        for worker in self.worker_addresses:
            healthcheck = Controller(worker)
            Controllers.append(healthcheck)
            thread = threading.Thread(target=healthcheck.send_healthcheck)
            self.threads.append(thread)

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()

        # Round-Trip Times am Ende von Threads sammeln
        for i, controller in enumerate(Controllers):
            self.results_rtts[self.worker_addresses[i]] = controller.get_rtts()

        return self.results_rtts


if __name__ == "__main__":
    num_Workers = int(os.getenv("WORKER_COUNT", "1"))
    base_port = int(os.getenv("WORKER_PORT", 12345))
    # base_name = os.getenv("WORKER_NAME", "worker")
    base_name = "worker"  # Name des Workers
    worker_addresses = []

    for i in range(1, num_Workers + 1):
        host = f"{base_name}-{i}"
        worker_addresses.append((host, base_port))

    manager = HealthCheckManager(worker_addresses)
    rtt_data = manager.start_healthchecks()

    for worker, rtts in rtt_data.items():
        print(f" RTTs für Worker {worker}: {rtts}")

    # rtt_data_str = {f"{addr[0]:addr[1]}": rtts for worker, rtts in rtt_data.items()}
    rtt_data_str = {f"{worker[0]}:{worker[1]}": rtts for worker, rtts in rtt_data.items()}

    # RTTs in eine JSON-Datei schreiben
    with open("rtts.json", "w") as file:
        json.dump(rtt_data_str, file, indent=4)

    print("RTTs in rtts.json gespeichert.")
