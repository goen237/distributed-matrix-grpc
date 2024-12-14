import socket
import os
import json
import time
import logging
import threading
import grpc
from concurrent import futures
import matrix_pb2
import matrix_pb2_grpc

# Konfiguration des Loggings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Worker:
    def __init__(self, udp_port: int, tcp_port: int):
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('0.0.0.0', self.udp_port))
        self.server_host = 'http_server'
        self.json_file = "/app/data/rtt_data.json"
        self.rtt_data = []

    def start(self):
        udp_thread = threading.Thread(target=self._start_udp, daemon=True)
        udp_thread.start()
        logger.info("UDP-Listener gestartet.")

    def _start_udp(self):
        try:
            while self.running:
                data, addr = self.udp_socket.recvfrom(1024)
                self._handle_udp_request(data, addr)
        except Exception as e:
            logger.error(f"Fehler im UDP Worker: {e}")
        finally:
            self.udp_socket.close()

    def _handle_udp_request(self, data: bytes, addr: tuple):
        if data.decode() == 'healthcheck':
            logger.info(f"Healthcheck-Anfrage von {addr} erhalten auf Port {self.udp_port}")
            self.udp_socket.sendto(b'OK', addr)
        elif data.decode() == 'stop':
            logger.info(f"Stop-Anfrage von {addr} erhalten auf Port {self.udp_port}")
            # self.running = False

    def send_request(self, request, retries=5, timeout=5):
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Versuch {attempt}/{retries}: Verbindung zum Server herstellen...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.settimeout(timeout)
                    start_time = time.time()
                    client_socket.connect((self.server_host, self.tcp_port))
                    client_socket.send(request.encode())
                    response = client_socket.recv(1024).decode()
                    end_time = time.time()
                    logger.info(f"Antwort erhalten: {response}")
                    rtt = round((end_time - start_time) * 1000, 2)
                    logger.info(f"RTT: {rtt} ms")
                    self.rtt_data.append(rtt)
                    return response
            except (socket.timeout, socket.error) as e:
                logger.warning(f"Fehler beim Versuch {attempt}/{retries}: {e}")
                last_exception = e

        raise last_exception

    def send_post(self, key, value):
        body = json.dumps({key: value})
        request = (f"POST / HTTP/1.1\r\nHost: {self.server_host}\r\nContent-Type: application/json\r\n"
                   f"Content-Length: {len(body)}\r\n\r\n{body}")
        return self.send_request(request)

    def send_get(self):
        request = f"GET / HTTP/1.1\r\nHost: {self.server_host}\r\n\r\n"
        return self.send_request(request)

    def read_json_file(self, rtt_data: dict):
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []

        data.append(rtt_data)
        with open(self.json_file, "w") as f:
            json.dump(data, f, indent=4)

        logger.info(f"RTT in {self.json_file} gespeichert.")


class MatrixServices(matrix_pb2_grpc.MatrixServiceServicer):
    def __init__(self, Worker):
        self.Worker = Worker
    def CalculateMatrix(self, request, context):
        if len(request.matrix_a) != len(request.matrix_b):
            context.set_details("Die Matrizen haben unterschiedliche Längen")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return matrix_pb2.MatrixResponse()

        try:
            result = sum(a * b for a, b in zip(request.matrix_a, request.matrix_b))
            return matrix_pb2.MatrixResponse(result=result)
        except Exception as e:
            logger.error(f"Fehler bei der Matrixberechnung: {e}")
            context.set_details("Fehler bei der Berechnung")
            context.set_code(grpc.StatusCode.INTERNAL)
            return matrix_pb2.MatrixResponse()

    def StoreMatrix(self, request, context):
        try:
            response = self.Worker.send_post(f"{request.row}/{request.col}", str(request.result))
            return matrix_pb2.StoreMatrixResponse(message="Matrix erfolgreich gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Matrix: {e}")
            context.set_details("Fehler beim Speichern")
            context.set_code(grpc.StatusCode.INTERNAL)
            return matrix_pb2.StoreMatrixResponse()


def serve(_worker: Worker):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    matrix_pb2_grpc.add_MatrixServiceServicer_to_server(MatrixServices(_worker), server)
    _port = int(os.getenv("WORKER_PORT", 12345))
    server.add_insecure_port(f'[::]:{_port}')
    server.start()
    logger.info(f"gRPC-Server gestartet auf Port {_port}.")
    server.wait_for_termination()


if __name__ == '__main__':

    worker = Worker(udp_port=12345, tcp_port=80)
    worker.start()

    rtt = {
        "Worker": os.getenv("CONTAINER_NAME", "unknown"),
        "RTT": worker.rtt_data
    }
    worker.read_json_file(rtt)

    serve(worker)
