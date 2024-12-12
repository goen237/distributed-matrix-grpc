import socket
import os
import json
import time
import logging
import grpc
from concurrent import futures
import matrix_pb2
import matrix_pb2_grpc


# Konfiguration des Loggings, damit die Ausgaben in der Konsole erscheinen
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Worker:
    def __init__(self, port: int):
        self.port = port
        self.running = True

    def start(self):
        raise NotImplementedError("Subclasses should implement this!")

    def handle_request(self, data: bytes, addr: tuple):
        raise NotImplementedError("Subclasses should implement this!")


class UDPWorker(Worker):
    def __init__(self, port: int):
        super().__init__(port)
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.port))
        self.running = True

    def start(self):
        logger.info(f"UDPWorker gestartet, wartet auf Anfragen auf Port {self.port} ...")
        try:
            while self.running:
                data, addr = self.sock.recvfrom(1024)
                self.handle_request(data, addr)
        except Exception as e:
            logger.error(f"Fehler im UDPWorker: {e}")
        finally:
            self.sock.close()

    def handle_request(self, data: bytes, addr: tuple):
        if data.decode() == 'healthcheck':
            logging.info(f"Healthcheck-Anfrage von Controller mit Adresse {addr} erhalten auf Port {self.port}")
            self.sock.sendto(b'OK', addr)
        elif data.decode() == 'stop':
            logging.info(f"Stop-Anfrage von Controller mit Adresse {addr} erhalten auf Port {self.port}")
            self.running = False

class HTTP_TCP_Worker(Worker):
    def __init__(self, port: int =80):
        super().__init__(port)
        self.server_host = 'http_server'
        self.server_port = port
        self.json_file = "/app/data/rtt_data.json"
        self.rtt_data = []

    def read_json_file(self, rtt_data: dict):
        # RTT in einei Json-Datei speichern
        try:
            with open(self.json_file, "r") as f:
                data= json.load(f)
        except FileNotFoundError:
            data = []

        data.append(rtt_data)
        with open(self.json_file, "w") as f:
            json.dump(data, f, indent=4)

        logging.info(f"RTT in {self.json_file} gespeichert.")

    def send_request(self, request, retries=5, timeout=5):
        """Sendet eine Anfrage an den Server mit mehreren Wiederholungsversuchen."""
        last_exception = None

        for attempt in range(1, retries + 1):
            try:
                logging.info(f"Versuch {attempt}/{retries}: Verbindung zum Server herstellen...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.settimeout(timeout)  # Setzt ein Timeout
                    start_time = time.time()
                    client_socket.connect((self.server_host, self.server_port))  # Verbindung aufbauen
                    client_socket.send(request.encode())  # Anfrage senden
                    response = client_socket.recv(1024).decode()  # Antwort empfangen
                    end_time = time.time()
                    logging.info(f"Antwort erhalten: {response}")
                    rtt = round((end_time - start_time) * 1000, 2)
                    logging.info(f"RTT: {rtt} ms")
                    self.rtt_data.append(rtt)
                    return response  # Erfolgreiche Antwort zurückgeben

            except socket.timeout:
                logging.warning(f"Timeout beim Versuch {attempt}/{retries}.")
                last_exception = Exception("Timeout beim Warten auf den Server.")
            except socket.error as e:
                logging.error(f"Fehler beim Verbinden zum Server: {e}")
                last_exception = e

        # Wenn alle Versuche fehlschlagen, Exception auslösen
        raise last_exception

    def send_post(self, key, value):
        body =json.dumps({key: value})
        request = f"POST / HTTP/1.1\r\nHost: {self.server_host}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        return self.send_request(request)

    def send_get(self):
        request = f"GET / HTTP/1.1\r\nHost: {self.server_host}\r\n\r\n"
        return self.send_request(request)
# \r\n dient als Zeilenumbruch, \r\n\r\n als Trennung zwischen Header und Body

# gRPC-Server bzw M^2-Server
class MatrixServices(matrix_pb2_grpc.MatrixServiceServicer):
    def CalculateMatrix(self, request, context):
        # Matrix-Berechnung durchführen
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
        # Matrix speichern in der Datenbank
        try:
            client = HTTP_TCP_Worker()
            response = client.send_post(str(request.row)+'/'+str(request.col), str(request.result))
            return matrix_pb2.StoreMatrixResponse(message="Matrix erfolgreich gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Matrix: {e}")
            context.set_details("Fehler beim Speichern")
            context.set_code(grpc.StatusCode.INTERNAL)
            return matrix_pb2.StoreMatrixResponse()

# gRPC-Server starten
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    matrix_pb2_grpc.add_MatrixServiceServicer_to_server(MatrixServices(), server)
    _port = int(os.getenv("WORKER_PORT", 12345))
    server.add_insecure_port(f'[::]:{_port}')
    server.start()
    logger.info(f"gRPC-Server gestartet auf Port {_port}.")
    server.wait_for_termination()


if __name__ == '__main__':
    _client = HTTP_TCP_Worker()

    # Test GET-Anfragen
    logging.info(f"GET Anfrage: {_client.send_get()}")

    # Test JSON-Datei schreiben
    rtt = {
        "Worker": os.getenv("CONTAINER_NAME", "unknown"),
        "RTT": _client.rtt_data
    }
    _client.read_json_file(rtt)

    port = int(os.getenv("WORKER_PORT", 12345))
    worker = UDPWorker(port)
    worker.start()

    serve()

    """
    Sendet eine Anfrage an den Server und empfängt die Antwort.

    Args:
        request (str): Die HTTP-Anfrage als String.
        retries (int): Anzahl der Wiederholungsversuche bei Verbindungsproblemen.
        timeout (int): Zeitlimit in Sekunden für die Verbindung und Antwort.

    Returns:
        str: Die HTTP-Antwort des Servers.

    Raises:
        Exception: Wenn die Verbindung fehlschlägt oder keine Antwort erhalten wird.
    """