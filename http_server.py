import socket
import json
import threading
import logging
import math

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db = []
        self.current_matrix = None
        self.data_array = []
        self.lock = threading.Lock()

    def add(self, data):
        with self.lock:
            self.db.append(data)
            logger.info(f"Neue Zeile hinzugefügt: {data}")


    def get_all(self):
        with self.lock:
            return list(self.db)

    def form_matrix_and_store(self):
        # Prüfen, ob die Anzahl der Elemente ein perfektes Quadrat ist
        if not math.sqrt(len(self.data_array)).is_integer() or len(self.data_array) < 4:
            logger.warning(f"Die Anzahl der Elemente -> {len(self.data_array)} <- ist kein perfektes Quadrat. Matrix kann nicht gebildet werden.")
            return None

        else:
            # Maximale Dimensionen der Matrix finden
            max_row = max(pos[0] for _, pos in self.data_array) + 1
            max_col = max(pos[1] for _, pos in self.data_array) + 1

            # Initialisiere eine leere Matrix mit Nullen
            matrix = [[0 for _ in range(max_col)] for _ in range(max_row)]

            # Platziere jedes Element an der angegebenen Position
            for element, (row, col) in self.data_array:
                matrix[row][col] = element

            matrix  = ['['+', '.join(map(str, matrix[i]))+']' for i in range(len(matrix))]
            self.current_matrix = matrix
            return matrix

    def get_current_matrix(self):
        return self.current_matrix


def handle_client(client_socket, db : Database):
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
            data = db.get_current_matrix()
            if data is not None:
                db.add(data)
                response_body = json.dumps({"Matrix_Resultaten": db.get_all()})
            else:
                response_body = json.dumps({"Message":"Matrix immer noch unvollständig ."})

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
            # Überprüfen, ob Content-Type application/json ist
            content_type = None
            for header in headers:
                if header.lower().startswith("content-type"):
                    content_type = header.split(":")[1].strip()
                    break

            if content_type != "application/json":
                response_body = json.dumps({"error": "Content-Type must be application/json"})
                response = (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                client_socket.sendall(response.encode('utf-8'))
                logger.warning("Content-Type ist nicht application/json.")
                return
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
            while len(body) < content_length:
                body += client_socket.recv(content_length - len(body)).decode('utf-8')

            try:
                # Füge die Daten in die DB ein
                data = json.loads(body)
                key, value = list(data.items())[0]
                row, col = key.split('/')
                row, col = int(row), int(col)
                db.data_array.append((value, (row, col)))
                db.form_matrix_and_store()
                response_body = json.dumps({"message": "Data added successfully"})
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                logger.info("POST-Anfrage erfolgreich bearbeitet.")
            except json.JSONDecodeError as e:
                response_body = json.dumps({"error": "Invalid JSON", "details": str(e)})
                response = (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "\r\n"
                    f"{response_body}"
                )
                client_socket.sendall(response.encode('utf-8'))
                logger.warning(f"Ungültiges JSON in der Anfrage. Fehler: {e}")


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

    db = Database()
    db.add([
    "[5, 48, 33]",
    "[78, 18, 65]",
    "[33, 45, 18]"
    ])
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(10)
        logger.info(f"Server gestartet unter http://{host}:{port}")
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {e}")
        return

    MAX_CLIENTS = 10
    current_clients = 0

    while True:
        client_socket, addr = server_socket.accept()
        current_clients += 1
        logger.info(f"Verbindung von {addr} hergestellt.")

        client_thread = threading.Thread(target=handle_client, args=(client_socket, db))
        client_thread.start()


if __name__ == "__main__":
    # mit 0.0.0.0 werden Anfragen von allen Netzwerkschnittstellen akzeptiert
    start_server("0.0.0.0", 80)
