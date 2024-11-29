import socket
import os
import json
import time

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
        print(f"Worker bereit, wartet auf Healthcheck-Anfragen auf Port {self.port} ...")
        while self.running:
            data, addr = self.sock.recvfrom(1024)
            self.handle_request(data, addr)
        self.sock.close()

    def handle_request(self, data: bytes, addr: tuple):
        if data.decode() == 'healthcheck':
            print(f"Healthcheck-Anfrage von Controller mit Adresse {addr} erhalten auf Port {self.port}")
            self.sock.sendto(b'OK', addr)
        elif data.decode() == 'stop':
            print(f"Stop-Anfrage von Controller mit Adresse {addr} erhalten auf Port {self.port}")
            self.running = False

class HTTP_TCP_Worker(Worker):
    def __init__(self, port: int =80):
        super().__init__(port)
        self.server_host = 'http_server'
        self.server_port = port
        #self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.bind(('0.0.0.0', self.port))
        #self.sock.listen(1)

    def send_request(self, request, retries=3, timeout=5):
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
        last_exception = None

        for attempt in range(1, retries + 1):
            try:
                print(f"Versuch {attempt}/{retries}: Verbindung zum Server herstellen...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.settimeout(timeout)  # Setzt ein Timeout
                    start_time = time.time()
                    client_socket.connect((self.server_host, self.server_port))  # Verbindung aufbauen
                    client_socket.send(request.encode())  # Anfrage senden
                    response = client_socket.recv(1024).decode()  # Antwort empfangen
                    end_time = time.time()
                    print("Antwort erhalten:", response)
                    print(f"RTT: {round((end_time - start_time) * 1000, 2)} ms")
                    return response  # Erfolgreiche Antwort zurückgeben

            except socket.timeout:
                print(f"Timeout beim Versuch {attempt}/{retries}.")
                last_exception = Exception("Timeout beim Warten auf den Server.")
            except socket.error as e:
                print(f"Fehler beim Verbinden zum Server: {e}")
                last_exception = e

        # Wenn alle Versuche fehlschlagen, Exception auslösen
        raise last_exception

    def send_post(self, key, value):
        body =json.dumps({key: value})
        #body = f"{key}={value}"
        request = f"POST / HTTP/1.1\r\nHost: {self.server_host}\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        return self.send_request(request)

    def send_get(self):
        request = f"GET / HTTP/1.1\r\nHost: {self.server_host}\r\n\r\n"
        return self.send_request(request)



if __name__ == '__main__':
    client = HTTP_TCP_Worker()

    # Test POST-Anfragen
    print("POST Anfrage: ", client.send_post("name", "Alice"))
    print("POST Anfrage: ", client.send_post("age", "30"))

    # Test GET-Anfragen
    print("GET Anfrage: ", client.send_get())

    port = int(os.getenv("WORKER_PORT", 12345))
    worker = UDPWorker(port)
    worker.start()

