Matrix-Berechnungs-Controller

## Übersicht
Das Programm `Controller` steuert verteilte Matrixberechnungen über mehrere Worker. Es übernimmt die Verteilung von Aufgaben, die Überwachung der Verfügbarkeit von Workern sowie das Speichern der Ergebnisse mittels UDP- und gRPC-Protokollen.

### Hauptfunktionen:
Das Programm bietet folgende Hauptfunktionen:

- **Health-Checks**: Überprüft die Erreichbarkeit von Workern über UDP.
- **Verteilte Berechnung**: Teilt Matrixberechnungen an erreichbare Worker aus und erhält Ergebnisse über gRPC..
- **RTT-Aufzeichnung**: Misst und speichert Round-Trip-Times (RTT) zu den Workern in einer JSON-Datei.
- **Aufgabenverteilung**: Verwendet ein Round-Robin-Verfahren, um Aufgaben gleichmäßig zu verteilen.
- **Ergebnisspeicherung**: Das Ergebnis wird an den entsprechenden Worker gesendet, der es in die Datenbank speichert und das Matrizergebnis dort bildet.

## Voraussetzungen

### Software
- Python 3.8 oder höher
- gRPC Python-Bibliotheken: grpcio, grpcio-tools
- Protokollpufferdateien: Module `matrix_pb2` und `matrix_pb2_grpc` (automatisch aus einer gRPC-Service-Definitionsdatei generiert).

### Umgebungsvariablen
- `WORKER_COUNT`: Anzahl der Worker im System (Standard: `3`).
- `WORKER_PORT`: Basisport, der von Workern verwendet wird (Standard: `12345`).

### Installation

1. Klonen Sie das Repository, das dieses Programm enthält.
2. Installieren Sie die notwendigen Bibliotheken:
    ```bash
    pip install grpcio grpcio-tools
    ```
3. Platzieren Sie die Dateien `matrix_pb2.py` und `matrix_pb2_grpc.py` im gleichen Verzeichnis wie das Hauptprogramm.


### Konfigurierbare Parameter
- **Matrixgrößen**: Zufällige Matrizen `matrix_a` und `matrix_b` werden mit der Größe `[3x3]` generiert. Sie können die Größen im Code anpassen.
- **Worker-Adressen**: Worker-Adressen werden dynamisch basierend auf den Umgebungsvariablen `WORKER_COUNT` und `WORKER_PORT` generiert.

### Health-Checks
Der Controller sendet eine `healthcheck`-Nachricht über UDP an jeden Worker, um die Verfügbarkeit zu überprüfen. Worker müssen mit `OK` antworten, um ihren Status zu bestätigen.

### Aufgabenverteilung
Die Aufgaben zur Matrizenmultiplikation werden über ein Round-Robin-Verfahren verteilt. Der Controller verwendet gRPC, um Berechnungsanfragen an Worker zu senden und die Ergebnisse abzurufen.

### Speicherung von RTT-Daten
Die RTT-Daten für jeden Worker werden in einer JSON-Datei (`/app/data/rtts.json`) gespeichert.

---

## Aufbau der Dateien
- **`controller.py`**: Hauptprogramm zur Kommunikation mit Workern, Aufgabenverteilung und Ergebnisspeicherung.
- **`matrix_pb2.py`**: Automatisch generierte gRPC-Protokollpufferdatei (nicht in diesem Dokument enthalten).
- **`matrix_pb2_grpc.py`**: Automatisch generierte gRPC-Service-Definitionen (nicht in diesem Dokument enthalten).

---

## Beispielausgabe
Beispielhafte Log-Ausgabe des Controllers:
```
2023-01-01 12:00:00 - INFO - Sende Healthcheck an group_d_2-worker-1:12345 ...
2023-01-01 12:00:01 - INFO - Healthcheck-Antwort von group_d_2-worker-1:12345 ist gesund. RTT: 15.23 ms
2023-01-01 12:00:01 - INFO - Weise Aufgabe (0, 1) Worker group_d_2-worker-2 zu...
2023-01-01 12:00:02 - INFO - Worker group_d_2-worker-2 hat Ergebnis berechnet: 45 für (0, 1)
2023-01-01 12:00:02 - INFO - RTTs werden in /app/data/rtts.json gespeichert.
```

## Beschreibung der Hauptmethoden

### `__init__(worker_addresses)`
Initialisiert den Controller mit einer Liste von Worker-Adressen.
- **Parameter**: `worker_addresses` - Liste von Tupeln mit IP und Port der Worker.
- **Aufgaben**:
  - Initialisierung des UDP-Sockets.
  - Setzen von Timeout-Werten.
  - Vorbereiten von RTT- und Status-Tracking-Mechanismen.

### `send_healthcheck(worker_address)`
Sendet einen UDP-Health-Check an einen Worker.
- **Parameter**: `worker_address` - Adresse des Workers als Tupel (IP, Port).
- **Aufgaben**:
  - Misst die RTT für den Worker.
  - Aktualisiert den Gesundheitsstatus des Workers.

### `start_healthchecks()`
Startet parallele Health-Checks für alle Worker.
- **Aufgaben**:
  - Erstellt Threads für jeden Worker.
  - Führt Health-Checks parallel aus.

### `calculate_matrix(worker_address, matrix_a, matrix_b, row, col)`
Berechnet das Ergebnis einer Matrixmultiplikation für eine Zelle.
- **Parameter**:
  - `worker_address`: Adresse des Workers.
  - `matrix_a`, `matrix_b`: Matrizen zur Berechnung.
  - `row`, `col`: Zielzeile und -spalte.
- **Rückgabe**: Berechnungsergebnis.

### `store_result(worker_address, result, row, col)`
Speichert das Ergebnis der Berechnung auf einem Worker.
- **Parameter**:
  - `worker_address`: Adresse des Workers.
  - `result`: Berechnetes Ergebnis.
  - `row`, `col`: Zielposition der Speicherung.
- **Rückgabe**: Erfolgsnachricht.

### `distribute_tasks(matrix_a, matrix_b)`
Verteilt die Aufgaben der Matrizenmultiplikation auf alle Worker.
- **Parameter**:
  - `matrix_a`, `matrix_b`: Eingabematrizen.
- **Aufgaben**:
  - Zerlegt die Matrizenmultiplikation in kleine Aufgaben.
  - Verteilt die Aufgaben an gesunde Worker im Round-Robin-Verfahren.

### `assign_task(task)`
Diese Methode weist eine Berechnungsaufgabe einem verfügbaren Worker zu.
- **Parameter**:

    -`task`: Ein Tupel bestehend aus Zeilenindex, Spaltenindex, Zeilendaten und Spaltendaten.
- **Aufgaben**:
  1. Wählt einen verfügbaren Worker im Round-Robin-Verfahren aus.
  2. Sendet die Berechnungsanfrage an den Worker.
  3. Speichert das Ergebnis, wenn die Berechnung erfolgreich ist.
  4. Handhabt Fehler, falls der Worker nicht erreichbar ist.

###

save_rtt_data(json_file)


Diese Methode speichert die Round-Trip-Time (RTT) Daten in einer JSON-Datei.
- **Parameter**:

json_file

 - Der Pfad zur JSON-Datei, in der die RTT-Daten gespeichert werden.
- **Funktionsweise**:
  1. Öffnet die angegebene JSON-Datei.
  2. Schreibt die RTT-Daten in die Datei.



### `save_rtt_data(json_file)`
Speichert RTT-Daten in einer JSON-Datei.
- **Parameter**: `json_file` - Pfad zur JSON-Datei.
- **Aufgaben**:
  - Speichert Worker-RTTs und andere Metadaten.

### `close_socket()`
Schließt den UDP-Socket.

## Beispielworkflow

1. **Health-Checks starten**:
   ```bash
   python controller.py
   ```
   Ausgabe:
   ```
   2023-01-01 12:00:00 - INFO - Sende Healthcheck an group_d_2-worker-1:12345 ...
   2023-01-01 12:00:01 - INFO - Healthcheck-Antwort von group_d_2-worker-1:12345 ist gesund. RTT: 15.23 ms
   ```

2. **RTT-Daten speichern**:
   RTT-Ergebnisse werden in der Datei `/app/data/rtts.json` abgelegt.

3. **Aufgaben verteilen**:
   Matrixmultiplikation wird durch die Methode `distribute_tasks` effizient ausgeführt. Beispiel:
   ```
   matrix_a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
   matrix_b = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
   controller.distribute_tasks(matrix_a, matrix_b)
   ```

# README: Worker-Modul

## Übersicht
Das `Worker`-Modul ist eine Komponente eines verteilten Systems zur Matrizenberechnung. Es kombiniert verschiedene Technologien wie MQTT, UDP und gRPC, um effizient Daten zu verarbeiten und mit anderen Modulen zu interagieren. Der Lamport-Algorithmus wird implementiert, um den Zugriff auf kritische Sektionen zu koordinieren.

---

## Hauptfunktionen
Das `Worker`-Modul bietet folgende Hauptfunktionen:

1. **Kommunikationsprotokolle**:
   - **UDP**: Bearbeitung von Healthcheck- und Stop-Signalen.
   - **MQTT**: Verwaltung von Request-, ACK- und Release-Nachrichten mit Lamport-Zeitstempeln.
   - **gRPC**: Bereitstellung von Matrizenberechnungs- und Speicheroperationen.
2. **Synchronisation**:
   - Zugriffskontrolle auf kritische Sektionen durch den Lamport-Algorithmus.
3. **RTT-Messung**:
   - Erfassung der Round-Trip-Time (RTT) bei TCP-Kommunikation.
4. **Datenpersistenz**:
   - Speicherung von RTT-Daten in einer JSON-Datei.

---

## Anforderungen

### Software
- **Python 3.8+**
- **Abhängigkeiten**:
  - `paho-mqtt`
  - `grpcio`
  - `grpcio-tools`

### Umgebungsvariablen
- `CONTAINER_NAME`: Name des Docker-Containers (Standard: "unknown").
- `WORKER_PORT`: Port für den gRPC-Server (Standard: `12345`).

---

## Installation
1. Installieren Sie die benötigten Bibliotheken:
   ```bash
   pip install paho-mqtt grpcio grpcio-tools
   ```
2. Stellen Sie sicher, dass die Dateien `matrix_pb2.py` und `matrix_pb2_grpc.py` generiert und verfügbar sind.
3. Starten Sie den Worker mit:
   ```bash
   python worker.py
   ```

---

## Architektur und Implementierung

### Lamport-Algorithmus
Der Worker implementiert den Lamport-Algorithmus, um konkurrierende Zugriffe auf kritische Sektionen zu koordinieren. Jeder Worker:
- Verwaltet eine logische Uhr (`clock`).
- Sendet und empfängt Nachrichten (`request`, `ack`, `release`) mit Zeitstempeln.
- Nutzt eine Prioritätswarteschlange (`queue`), um die Reihenfolge der Zugriffe zu bestimmen.

### Hauptklassen und Methoden

#### Klasse `Worker`

**Attribute:**
- `udp_port`, `tcp_port`: Kommunikationsports für UDP und TCP.
- `mqtt_host`, `mqtt_port`: Verbindungskonfiguration für den MQTT-Broker.
- `clock`: Logische Uhr für Lamport-Zeitstempel.
- `queue`: Prioritätswarteschlange für kritische Sektionen.
- `rtt_data`: Liste zur Speicherung der RTT-Werte.

**Methoden:**

- `__init__(udp_port, tcp_port, mqtt_host, mqtt_port)`:
  - Initialisiert den Worker mit den notwendigen Konfigurationsparametern.
  - Startet den MQTT-Client und bindet ihn an die entsprechenden Topics (`worker/request`, `worker/ack`, `worker/release`).

- `start()`:
  - Startet den UDP-Listener in einem separaten Thread.

- `_start_udp()`:
  - Verarbeitet eingehende UDP-Anfragen wie `healthcheck` und `stop`.

- `_on_message(client, userdata, message)`:
  - Callback-Methode für MQTT-Nachrichten. Bearbeitet eingehende Nachrichten basierend auf ihrem Topic (`request`, `ack`, `release`).

- `request_critical_section()`:
  - Fordert den Zugriff auf die kritische Sektion an.
  - Sendet eine `request`-Nachricht mit aktuellem Zeitstempel.
  - Wartet auf den Erhalt aller benötigten `ack`-Nachrichten.

- `release_critical_section()`:
  - Gibt die kritische Sektion frei und sendet eine `release`-Nachricht an andere Worker.

- `send_request(request, retries=5, timeout=5)`:
  - Sendet eine TCP-Anfrage an den Server und misst die RTT.

- `read_json_file(rtt_data)`:
  - Fügt neue RTT-Daten zu einer JSON-Datei hinzu.

#### Klasse `MatrixServices`
Diese Klasse implementiert die gRPC-Services des Workers.

- `CalculateMatrix(request, context)`:
  - Berechnet das Skalarprodukt zweier Matrizen.
  - Validiert die Eingabeparameter und gibt Fehlerstatus zurück, falls die Eingaben ungültig sind.

- `StoreMatrix(request, context)`:
  - Speichert das Ergebnis einer Matrizenoperation.
  - Nutzt den Lamport-Algorithmus, um den Zugriff auf die Ressource zu synchronisieren.

#### Methode `serve(worker)`
Startet den gRPC-Server und bindet die `MatrixServices` an den angegebenen Worker.

---

## Beispielworkflow

### 1. Worker starten
Starten Sie den Worker mit:
```bash
python worker.py
```

### 2. UDP-Healthcheck
Senden Sie eine Healthcheck-Anfrage:
```python
udp_socket.sendto(b'healthcheck', ('worker_ip', 12345))
```

### 3. Matrizenberechnung
Verwenden Sie den gRPC-Service `CalculateMatrix`:
```python
stub = matrix_pb2_grpc.MatrixServiceStub(channel)
response = stub.CalculateMatrix(
    matrix_pb2.MatrixRequest(matrix_a=[1, 2, 3], matrix_b=[4, 5, 6])
)
```

### 4. Speicherung eines Ergebnisses
Speichern Sie das Ergebnis einer Operation:
```python
stub.StoreMatrix(matrix_pb2.StoreMatrixRequest(row=0, col=0, result=42))
```


# README: Einfacher Matrix-Datenbank-HTTP-Server

## Überblick
Dieser Server bietet eine einfache Implementierung eines HTTP-Servers zur Verwaltung und Verarbeitung von Matrizen. Er unterstützt:

- Speicherung von Matrixdaten über POST-Anfragen.
- Abruf von Matrixdaten und gespeicherten Ergebnissen über GET-Anfragen.

Der Server verwendet Python-Sockets und ist multithreaded, um mehrere gleichzeitige Verbindungen zu verarbeiten.

---

## Hauptfunktionen

### GET-Anfragen
- **Pfad**: `/`
- **Beschreibung**: Gibt die aktuelle Matrix und alle gespeicherten Ergebnisse zurück.
- **Rückgabe**:
  - Wenn eine Matrix erfolgreich erstellt wurde:
    ```json
    {
      "Matrix_Resultaten": [
        [Matrix1],
        [Matrix2],
        ...
      ]
    }
    ```
  - Wenn die Matrix unvollständig ist:
    ```json
    {
      "Message": "Matrix immer noch unvollständig."
    }
    ```

### POST-Anfragen
- **Pfad**: `/`
- **Content-Type**: `application/json`
- **Beschreibung**: Fügt ein neues Element in die Matrix ein. Die Daten sollten das folgende Format haben:
  ```json
  {
    "Zeile/Spalte": Wert
  }
  ```
  Beispiel:
  ```json
  {
    "0/0": 5
  }
  ```
- **Antwort**:
  - Erfolgreiches Hinzufügen:
    ```json
    {
      "message": "Data added successfully"
    }
    ```
  - Fehlerhafte Anfrage (z. B. ungültiges JSON):
    ```json
    {
      "error": "Invalid JSON",
      "details": "..."
    }
    ```

---

## Anforderungen

### Software
- **Python 3.8+**

### Bibliotheken
Keine externen Bibliotheken erforderlich.

---

## Installation und Ausführung

1. **Klonen oder Herunterladen des Repositories**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Starten des Servers**:
   ```bash
   python server.py
   ```
   Der Server wird standardmäßig auf `http://0.0.0.0:80` ausgeführt.

---

## Beispiele

### GET-Anfrage
```bash
curl -X GET http://localhost:80/
```
**Antwort (Beispiel)**:
```json
{
  "Matrix_Resultaten": [
    ["[1, 2]", "[3, 4]"]
  ]
}
```

### POST-Anfrage
```bash
curl -X POST -H "Content-Type: application/json" -d '{"0/0": 1}' http://localhost:80/
```
**Antwort**:
```json
{
  "message": "Data added successfully"
}
```

---

## Interne Logik

### Matrixbildung
- Elemente werden als Tupel `(Wert, (Zeile, Spalte))` in einer internen Liste gespeichert.
- Wenn die Anzahl der Elemente ein perfektes Quadrat ist und mindestens 4 Einträge existieren, wird die Matrix erstellt und gespeichert.

### Multithreading
- Jeder eingehende Client wird in einem separaten Thread verarbeitet, um gleichzeitige Anfragen zu unterstützen.

### Fehlerbehandlung
- Ungültige JSON-Daten oder unvollständige Anfragen werden mit aussagekräftigen Fehlermeldungen beantwortet.

## Docker-Setup

### Docker-Compose

Das Projekt verwendet Docker-Compose, um die verschiedenen Dienste zu orchestrieren. Die `docker-compose.yml`-Datei definiert die Konfiguration für die folgenden Dienste:

- **mqtt-broker**: Ein MQTT-Broker basierend auf Eclipse Mosquitto.
- **worker**: Ein Worker-Dienst, der Matrizenberechnungen durchführt.
- **controller**: Der Controller-Dienst, der die Worker steuert und die Aufgaben verteilt.
- **http_server**: Ein einfacher HTTP-Server zur Verwaltung und Verarbeitung von Matrizen.

#### Beispiel für `docker-compose.yml`

```yaml
version: '3.8'
services:
  mqtt-broker:
    image: eclipse-mosquitto
    container_name: mqtt-broker
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
    ports:
      - "1883:1883"
    networks:
      - app-network

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - WORKER_PORT=12345
      - CONTAINER_NAME=${HOSTNAME:-default_hostname}
      - WORKER_COUNT=${WORKER_COUNT}
    depends_on:
      - mqtt-broker
    volumes:
      - ./data/rtt_data.json:/app/data/rtt_data.json
      - ./worker.py:/app/worker.py
      - ./matrix.proto:/app/matrix.proto
    networks:
      - app-network
      - grpc-network
    deploy:
      replicas: ${WORKER_COUNT}
      endpoint_mode: dnsrr
    entrypoint: ["python", "worker.py"]

  controller:
    build:
      context: .
      dockerfile: Dockerfile.controller
    container_name: controller
    depends_on:
      - worker
    volumes:
      - ./rtts.json:/app/data/rtts.json
      - ./controller.py:/app/controller.py
      - ./matrix.proto:/app/matrix.proto
    networks:
      - app-network
      - grpc-network
    environment:
      - WORKER_COUNT=${WORKER_COUNT}
    entrypoint: ["python", "controller.py"]

  http_server:
    build:
      context: .
      dockerfile: Dockerfile.http_server
    container_name: http_server
    networks:
      - app-network
    ports:
      - "8080:80"
    volumes:
      - ./http_server.py:/usr/src/app/http_server.py
    environment:
      - WORKER_COUNT=${WORKER_COUNT}
    entrypoint: ["python", "http_server.py"]

networks:
  app-network:
    driver: bridge
  grpc-network:
    driver: bridge
```

### Makefile

Das Makefile enthält verschiedene Befehle, um die Docker-Umgebung zu verwalten. Es ermöglicht das Starten, Stoppen und Skalieren der Docker-Container sowie das Ausführen des Controllers.

#### Beispiel für `Makefile`

```makefile
workers ?= 3

.PHONY: up scale down run-Controller

start:
  @echo "Démarrage de Docker-Compose avec ${workers} Worker-Replikaten..."
  @set "WORKER_COUNT=${workers}" && docker-compose build

up:
  @set "WORKER_COUNT=${workers}" && docker-compose up -d --scale worker=${workers}

down:
  @echo "Stoppe und entferne Docker-Compose-Umgebung..."
  @set "WORKER_COUNT=${workers}" && docker-compose down

scale:
  @echo "Skaliere die Anzahl der Worker auf ${workers}..."
  @set "WORKER_COUNT=${workers}" && docker-compose up -d --scale worker=${workers}

run-Controller:
  @echo "Führe Controller aus..."
  @docker-compose exec controller python3 controller.py
```

### Verwendung

1. **Starten der Umgebung**:
   ```bash
   make start
   ```

2. **Hochfahren der Container**:
   ```bash
   make up
   ```

3. **Herunterfahren der Container**:
   ```bash
   make down
   ```

4. **Skalieren der Worker**:
   ```bash
   make scale workers=5
   ```

5. **Controller ausführen**:
   ```bash
   make run-Controller
   ```

Diese Befehle erleichtern die Verwaltung der Docker-Container und die Durchführung von Aufgaben innerhalb der Container.