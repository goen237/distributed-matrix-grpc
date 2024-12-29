import paho.mqtt.client as mqtt
from queue import PriorityQueue
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
    def __init__(self, udp_port: int, tcp_port: int, mqtt_host: str, mqtt_port: int):
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('0.0.0.0', self.udp_port))
        self.server_host = 'http_server'
        self.json_file = "/app/data/rtt_data.json"
        self.rtt_data = []

        # Lamport-Algorithmus
        self.clock = 0
        self.queue = PriorityQueue()
        self.mutex = threading.Lock()
        # eigene IP-Adresse ermitteln
        self.ip_address = socket.gethostbyname(socket.gethostname())

        # MQTT-Client
        self.mqtt_brocker = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_client = mqtt.Client(client_id=str(self.ip_address), protocol=mqtt.MQTTv311)
        self.mqtt_client.on_message = self._on_message
        try:
            self.mqtt_client.connect(self.mqtt_brocker, self.mqtt_port, 60)
            logger.info(f"Erfolgreich verbunden mit MQTT-Broker {self.mqtt_brocker}:{self.mqtt_port}")
        except Exception as e:
            logger.error(f"Fehler beim Verbinden mit dem MQTT-Broker: {e}")

        self.mqtt_client.subscribe("worker/request")
        self.mqtt_client.subscribe("worker/ack")
        self.mqtt_client.subscribe("worker/release")
        self.mqtt_client.loop_start()

    def  start(self):
        logger.info(f"IP-Adresse: {self.ip_address}")
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

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload = json.loads(message.payload.decode())
        logger.info(f"Nachricht erhalten auf Topic: {topic} - {payload}")

        if topic == "worker/request":
            self._handle_request(payload)
        elif topic == "worker/ack":
            self._handle_ack(payload)
        elif topic == "worker/release":
            self._handle_release(payload)

    def _handle_request(self, request):
        with self.mutex:
            self.clock = max(self.clock, request["timestamp"]) + 1
            self.queue.put((request["timestamp"], request["ip"]))
            self.mqtt_client.publish("worker/ack", json.dumps({
                "timestamp": self.clock,
                "ip": self.ip_address
            }))
            logger.info(f"ACK gesendet an {request['ip']}")

    def _handle_ack(self, ack):
        with self.mutex:
            self.clock = max(self.clock, ack["timestamp"]) + 1
            self.queue.put((ack["timestamp"], ack["ip"]))

    def _handle_release(self, release):
        with self.mutex:
            self.clock = max(self.clock, release["timestamp"]) + 1
            while not self.queue.empty() and self.queue.queue[0][1] != self.ip_address:
                self.queue.get()

    def request_critical_section(self):
        with self.mutex:
            self.clock += 1
            self.queue.put((self.clock, self.ip_address))
            self.mqtt_client.publish("worker/request", json.dumps({
                "timestamp": self.clock,
                "ip": self.ip_address
            }))

        while self.queue.queue[0][1] != self.ip_address:
            pass

    def release_critical_section(self):
        with self.mutex:
            self.queue.get()
            self.mqtt_client.publish("worker/release", json.dumps({
                "timestamp": self.clock,
                "ip": self.ip_address
            }))


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
                   f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}")
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
            self.Worker.request_critical_section()
            response = self.Worker.send_post(f"{request.row}/{request.col}", str(request.result))
            self.Worker.release_critical_section()
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

    worker = Worker(udp_port=12345, tcp_port=80, mqtt_host="mqtt-broker", mqtt_port=1883)
    worker.start()

    rtt = {
        "Worker": os.getenv("CONTAINER_NAME", "unknown"),
        "RTT": worker.rtt_data
    }
    worker.read_json_file(rtt)

    serve(worker)
