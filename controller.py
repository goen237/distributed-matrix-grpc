import socket
import time
import threading
import os
import json
import random
import grpc
import logging
import matrix_pb2
import matrix_pb2_grpc
from concurrent.futures import ThreadPoolExecutor


# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, worker_address: list):
        self.worker_addresses = worker_addresses
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.health_status = {addr: False for addr in worker_addresses}
        self.rtts = {addr: [] for addr in worker_addresses}  # RTT-Daten für jeden Worker
        self.task_assignment_index = 0  # Index für Round-Robin-Aufgabenzuweisung


    def send_healthcheck(self, worker_address: list):
        address, port = worker_address
        try:
            logger.info(f"Sending Healthcheck to {address}:{port} ...")
            start_time = time.time()
            self.sock.sendto(b'healthcheck', (address, port))
            data, _ = self.sock.recvfrom(1024)
            end_time = time.time()

            if data.decode() == 'OK':
                rtt = round((end_time - start_time) * 1000, 2)  # RTT in Millisekunden
                self.rtts[worker_address].append(rtt)
                self.health_status[worker_address] = True
                logger.info(f"Healthcheck response from {address}:{port} is healthy. RTT: {rtt} ms")
                # Ping an den Worker senden und RTT zurückgeben
                #os.system(f"ping -c 1 {address}")
            else:
                logger.warning(f"Unexpected response from {address}->{port}: {data.decode()}")
        except socket.timeout:
            logger.warning(f"No response from {address}:{port} (Timeout).")
            self.rtts.append(None)

    def start_healthchecks(self):
        """Startet die Healthchecks gleichzeitig für alle Worker."""

        threads = []
        for worker_address in self.worker_addresses:
            thread = threading.Thread(target=self.send_healthcheck, args=(worker_address,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def calculate_matrix(self, worker_address, matrix_a, matrix_b, row, col):
        """Berechnet die Matrix mit einem Worker."""
        address, _ = worker_address
        with grpc.insecure_channel(f"{address}:12345") as channel:
            stub = matrix_pb2_grpc.MatrixServiceStub(channel)
            response = stub.CalculateMatrix(
                matrix_pb2.MatrixRequest(matrix_a=matrix_a, matrix_b=matrix_b, row=row, col=col)
            )
            return response.result

    def store_result(self, worker_address, result, row, col):
        """Speichert das Berechnungsergebnis beim Worker."""
        address, _ = worker_address
        with grpc.insecure_channel(f"{address}:12345") as channel:
            stub = matrix_pb2_grpc.MatrixServiceStub(channel)
            response = stub.StoreMatrix(
                matrix_pb2.StoreRequest(result=result, row=row, col=col)
            )
            return response.message


    def distribute_tasks(self, matrix_a, matrix_b):
        """Verteilt die Berechnungsaufgaben auf die erreichbaren Worker."""
        line_ma = len(matrix_a)
        column_ma = len(matrix_a[0])
        line_mb = len(matrix_b)
        column_mb = len(matrix_b[0])

        if column_ma != line_mb:
            logger.error("The number of columns of the first matrix must be equal to the number of lines of the second matrix.")
            return

        task_queue = []
        for i in range(line_ma):
            for j in range(column_mb):
                column = [matrix_b[k][j] for k in range(line_mb)]
                task_queue.append((i, j, matrix_a[i], column))

        def assign_task(task):
            row, col, row_data, column_data = task
            for _ in range(len(self.worker_addresses)):
                # Wähle den nächsten verfügbaren Worker im Round-Robin-Verfahren
                worker_address = self.worker_addresses[self.task_assignment_index]
                self.task_assignment_index = (self.task_assignment_index + 1) % len(self.worker_addresses)
                if self.health_status.get(worker_address):
                    try:
                        logger.info(f"Assigning task ({row}, {col}) to Worker {worker_address}...")
                        result = self.calculate_matrix(worker_address, row_data, column_data, row, col)
                        logger.info(f"Worker {worker_address} calculated result: {result} for ({row}, {col})")
                        self.store_result(worker_address, result, row, col)
                        return
                    except grpc.RpcError as e:
                        logger.error(f"Worker {worker_address} failed: {e}")

        with ThreadPoolExecutor(max_workers=len(self.worker_addresses)) as executor:
            executor.map(assign_task, task_queue)


    '''def calculate_and_store(self, matrix_a, matrix_b, row, col):
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
    def save_rtt_data(self, json_file):
            """Speichert die RTT-Daten in einer JSON-Datei."""
            rtt_data = {
                "Workers": len(self.worker_addresses),
                "RTTs": [
                    {"Worker": f"{worker[0]}:{worker[1]}", "RTT": rtts}
                    for worker, rtts in self.rtts.items()
                ]
            }
            with open(json_file, "w") as f:
                json.dump(rtt_data, f, indent=4)
            logger.info(f"RTTs saved to {json_file}.")

    def close_socket(self):
        self.sock.close()


if __name__ == "__main__":
    num_workers = int(os.getenv("WORKER_COUNT", "3"))
    base_port = int(os.getenv("WORKER_PORT", "12345"))
    base_name = "group_d_2-worker"  # Name des Workers
    # Worker-Adressen erstellen
    worker_addresses = [
        (f"{base_name}-{i}", base_port) for i in range(1, num_workers + 1)
    ]

    json_file = "/app/data/rtts.json"

    matrix_a = [[random.randint(1, 10) for _ in range(3)] for _ in range(3)]
    matrix_b = [[random.randint(1, 10) for _ in range(3)] for _ in range(3)]




    controller = Controller(worker_addresses)

    logger.info("Starting healthchecks...")
    controller.start_healthchecks()

    logger.info("Saving RTT data...")
    rtt_file = "/app/data/rtts.json"
    controller.save_rtt_data(rtt_file)

    logger.info("Distributing matrix computation tasks...")
    controller.distribute_tasks(matrix_a, matrix_b)

    controller.close_socket()


    # Matrixberechnung und Speicherung
    '''if column_ma != line_mb:
        logger.error("The number of columns of the first matrix must be equal to the number of lines of the second matrix.")
    else:
        for i in range(line_ma):
            line = matrix_a[i]
            c = -1
            for j in range (column_mb):
                column =[]
                for k in range(line_mb):
                    column.append(matrix_b[k][j])
                c += 1
                manager.calculate_and_store(line, column, i, c)'''


    while True:
        running = True

