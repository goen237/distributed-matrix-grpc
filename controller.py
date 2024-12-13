import socket
import time
import threading
import os
import json
import grpc
import logging
import matrix_pb2
import matrix_pb2_grpc
import random

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, worker_address: tuple, interval: int = 5):
        self.worker_address = worker_address
        self.interval = interval
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.rtts = []  # Round-Trip-Times Liste für die Worker

    def send_healthcheck(self):
        address, port = self.worker_address
        for attempt in range(5):  # 5 Healthchecks pro Worker
            try:
                logger.info(f"Sending Healthcheck to {address}:{port} (Attempt {attempt + 1}/5)...")
                start_time = time.time()
                self.sock.sendto(b'healthcheck', (address, port))

                data, _ = self.sock.recvfrom(1024)
                end_time = time.time()

                if data.decode() == 'OK':
                    rtt = round((end_time - start_time) * 1000, 2)  # RTT in Millisekunden
                    self.rtts.append(rtt)
                    logger.info(f"Healthcheck response from {address}:{port}: OK | RTT: {rtt} ms")
                    # Ping an den Worker senden und RTT zurückgeben
                    os.system(f"ping -c 1 {address}")
                else:
                    logger.warning(f"Unexpected response from {address}->{port}: {data.decode()}")

            except socket.timeout:
                logger.warning(f"No response from {address}:{port} (Timeout).")
                self.rtts.append(None)
            time.sleep(self.interval)
        self.sock.sendto(b'stop', (address, port))

    def get_rtts(self):
        return self.rtts  # Liefert die Round-Trip-Times Liste zurück

    def close_socket(self):
        self.sock.close()

    def calculate_matrix(self, worker_id, matrix_a, matrix_b, row, col):
        """Berechnet eine Matrix mit Hilfe eines Workers."""
        address, _ = self.worker_address
        with grpc.insecure_channel(f"{address}:12345") as channel:
            stub = matrix_pb2_grpc.MatrixServiceStub(channel)
            response = stub.CalculateMatrix(
                matrix_pb2.MatrixRequest(worker_id=worker_id, matrix_a=matrix_a, matrix_b=matrix_b, row=row, col=col)
            )
            return response.result

    def store_result(self, worker_id, result, row, col):
        """Speichert das Berechnungsergebnis beim Worker."""
        address, _ = self.worker_address
        with grpc.insecure_channel(f"{address}:12345") as channel:
            stub = matrix_pb2_grpc.MatrixServiceStub(channel)
            response = stub.StoreMatrix(matrix_pb2.StoreRequest(worker_id=worker_id, result=result, row=row, col=col))
            return response.message

class HealthCheckManager:
    def __init__(self, worker_addresses: list):
        self.worker_addresses = worker_addresses
        self.worker_choice = worker_addresses[:]
        self.threads = []
        self.results_rtts = {}  # Dictionary für die Round-Trip-Times
        self.controllers = []  # Liste aller Controller-Instanzen

    def start_healthchecks(self):
        """Startet die Healthchecks für alle Worker."""
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



    def calculate_and_store(self, matrix_a, matrix_b, row, col):
        """Berechnet Matrizen und speichert die Ergebnisse."""
        for worker_id, worker_address in enumerate(self.worker_choice):
            worker_id = random.randint(0, len(self.worker_choice) - 1)
            worker_address = self.worker_choice[worker_id]
            logger.info(f"Calculating and storing matrix at position ({row}, {col}) with Worker -> {worker_id, worker_address}...")
            try:
                controller = Controller(worker_address)
                result = controller.calculate_matrix(worker_id, matrix_a, matrix_b, row, col)
                logger.info(f"Worker {worker_address[0]} calculation result: {result} at position ({row}, {col})")
                message = controller.store_result(worker_id, result, row, col)
                logger.info(f"Worker {worker_address[0]} store message: {message}")
                self.worker_choice.remove(worker_address)
                return
            except grpc.RpcError as e:
                logger.error(f"Worker {worker_address[0]} failed: {e}")
        logger.error("All workers failed to calculate and store the matrix.")

'''
    def calculate_and_store_threaded(self, matrix_a, matrix_b, row, col):
        """Startet die Berechnung und Speicherung in einem Thread."""
        _thread = threading.Thread(target=self.calculate_and_store, args=(matrix_a, matrix_b, row, col))
        _thread.start()
        _thread.join()
'''


def read_existing_data(json_file):
    """Liest vorhandene Daten aus einer JSON-Datei."""
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            return json.load(f)
    return []



def save_rtt_data(json_file, num_workers, rtt_data):
    """Speichert RTT-Daten in einer JSON-Datei."""
    existing_data = read_existing_data(json_file)
    new_data = {
        "Workers": num_workers,
        "RTTs": [
            {"Worker": f"{worker[0]}:{worker[1]}", "RTT": rtts}
            for worker, rtts in rtt_data.items()
        ]
    }
    existing_data.append(new_data)
    with open(json_file, "w") as f:
        json.dump(existing_data, f, indent=4)
    logger.info(f"RTTs saved to {json_file}.")



if __name__ == "__main__":
    num_workers = int(os.getenv("WORKER_COUNT", "1"))
    base_port = int(os.getenv("WORKER_PORT", "12345"))
    base_name = "group_d_2-worker"  # Name des Workers
    worker_addresses = []

    json_file = "/app/data/rtts.json"

    matrix_a = [
        [1, 1, 3],
        [5, 2, 6],
        [2, 3, 4]
    ]

    matrix_b = [
        [1, 1, 3],
        [5, 2, 6],
        [-2, -1, -3]
    ]

    line_ma = len(matrix_a)
    column_ma = len(matrix_a[0])
    line_mb = len(matrix_b)
    column_mb = len(matrix_b[0])

     # Worker-Adressen erstellen
    worker_addresses = [
        (f"{base_name}-{i}", base_port) for i in range(1, num_workers + 1)
    ]

    # Healthchecks starten
    manager = HealthCheckManager(worker_addresses)
    rtt_data = manager.start_healthchecks()

    # Ergebnisse anzeigen und speichern
    for worker, rtts in rtt_data.items():
        logger.info(f"RTTs for Worker {worker}: {rtts}")

    save_rtt_data(json_file, num_workers, rtt_data)

    # Matrixberechnung und Speicherung
    if column_ma != line_mb:
        logger.error("The number of columns of the first matrix must be equal to the number of lines of the second matrix.")
    else:
        # manager.calculate_and_store(matrix_a, matrix_b)
        for i in range(line_ma):
            line = matrix_a[i]
            c = -1
            for j in range (column_mb):
                column =[]
                for k in range(line_mb):
                    column.append(matrix_b[k][j])
                c += 1
                manager.calculate_and_store(line, column, i, c)


    while True:
        running = True

