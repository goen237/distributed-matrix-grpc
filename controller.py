import socket
import time
# from typing import List, Tuple

def udp_controller(worker_addresses):
    # Ein Socket wird erstellt und an einen beliebigen Port gebunden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # Timeout für die Antwort

    # Jeder Worker in der Liste wird einzeln abgefragt
    for worker in worker_addresses:
        # Worker-Adresse und Port werden aus der Liste gelesen
        address, port = worker # Tuple unpacking

        # Startzeit für die Round-Trip-Time
        start_time = time.time()
        print(f"Sende Healthcheck an Worker bei {address}:{port} ...")

        sock.sendto(b'healthcheck', (address, port))  # Healthcheck senden

        try:
            data, _ = sock.recvfrom(1024)  # Antwort vom Worker empfangen

            # Endzeit für die Round-Trip-Time
            end_time = time.time()

            if data.decode() == 'OK':
                print(f"Antwort von Worker {address}:{port} erhalten: OK")
                sock.sendto(b'stop', (address, port))
            
            # Round-Trip-Time berechnen und ausgeben
            print(f"Round-Trip-Time: {(end_time - start_time) * 1000:.2f} ms\n")

        except socket.timeout:
            print(f"Keine Antwort vom Worker {address}:{port} erhalten.\n")

    # Socket schließen
    sock.close()

if __name__ == '__main__':
    # Worker-Adressen und Ports
    worker_addresses = [('localhost', 12345)]
    udp_controller(worker_addresses)
