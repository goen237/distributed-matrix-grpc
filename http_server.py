import socket
import json
import threading
import logging

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class HTTP_Server:
    def __init__(self):
        self.db = []
        self.lock = threading.Lock()

    def add(self, data):
        with self.lock:
            self.db.append(data)
            logger.info(f"Neue Zeile hinzugefügt: {data}")

    def get_all(self):
        with self.lock:
            return list(self.db)

def handle_client(client_socket, db):
    try:
        # Empfang der Anfrage
        request = client_socket.recv(1024).decode('utf-8')
        logger.info(f"Anfrage erhalten:\n{request}")  # Debugging line to see the raw request

        # HTTP-Header analysieren
        headers = request.split('\r\n')
        logger.debug(f"Headers:\n{headers}")  # Debugging line to check headers

        # Check if the request line has three parts
        try:
            method, path, _ = headers[0].split(' ')
        except ValueError:
            logger.warning(f"Ungültige Anfragezeile: {headers[0]}")
            return  # Handle error or send 400 Bad Request response

        if method == "GET" and path == "/":
            # GET-Anfrage bearbeiten
            response_body = json.dumps({"data": db.get_all()})
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "\r\n"
                f"{response_body}"
            )
            client_socket.sendall(response.encode('utf-8'))
            logger.info("GET-Anfrage erfolgreich bearbeitet.")

        elif method == "POST" and path == "/":
            # POST-Anfrage bearbeiten
            # Extrahiere den Body der Anfrage
            content_length = 0
            for header in headers:
               if header.lower().startswith("content-length"):
                    # 1. Teile den String 'header' an jedem ':' und erhalte eine Liste
                    teile = header.split(":")
                    # 2. Nimm das zweite Element der Liste (Index 1) und entferne Leerzeichen
                    zweites_element = teile[1].strip()
                    # 3. Konvertiere das bereinigte Element in eine Ganzzahl
                    content_length = int(zweites_element)

            body = request.split("\r\n\r\n")[1]  # Body nach den Headers
            if len(body) < content_length:
                body += client_socket.recv(content_length - len(body)).decode('utf-8')

            try:
                # Füge die Daten in die DB ein
                data = json.loads(body)
                db.add(data)
                response_body = json.dumps({"message": "Data added successfully"})
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                logger.info("POST-Anfrage erfolgreich bearbeitet.")
            except json.JSONDecodeError:
                response_body = json.dumps({"error": "Invalid JSON"})
                response = (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                logger.warning("Ungültiges JSON in der Anfrage.")
            client_socket.sendall(response.encode('utf-8'))

        else:
            # Nicht unterstützte Methode
            response_body = json.dumps({"error": "Not Implemented"})
            response = (
                "HTTP/1.1 501 Not Implemented\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "\r\n"
                f"{response_body}"
            )
            client_socket.sendall(response.encode('utf-8'))
            logger.warning(f"Nicht unterstützte Methode: {method}")


    finally:
        # Verbindung schließen
        client_socket.close()
        logger.info("Verbindung geschlossen.")


def start_server(host, port):

    db = HTTP_Server()
    db.add({
    "matrix_a": [5,48,84,84,8754,45],
    "matrix_b": [78,18,65,41,486,65],
    "result": [745,45,548,4,48,848]
    })
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(10)
    logger.info(f"Server gestartet unter http://{host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")

        client_thread = threading.Thread(target=handle_client, args=(client_socket, db))
        client_thread.start()



if __name__ == "__main__":
    start_server("0.0.0.0", 80)
