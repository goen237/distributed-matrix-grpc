import socket
import time
import threading
import os
# from typing import List, Tuple

def send_healthcheck(worker_addresses):
    # Ein Socket wird erstellt und an einen beliebigen Port gebunden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)  # Timeout für die Antwort


    # Worker-Adresse und Port werden aus der Liste gelesen
    address, port = worker_addresses # Tuple unpacking

    # Startzeit für die Round-Trip-Time
    start_time = time.time()
    print(f"Sende Healthcheck an Worker bei {address}:{port} ...")

    sock.sendto(b'healthcheck', (address, port))  # Healthcheck senden

    try:
        data, _ = sock.recvfrom(1024)  # Antwort vom Worker empfangen

        # Endzeit für die Round-Trip-Time
        end_time = time.time()

        if data.decode() == 'OK':
            print(f"Antwort von Worker {address} : {port} erhalten: OK")
            sock.sendto(b'stop', (address, port))
        
        # Round-Trip-Time berechnen und ausgeben
        print(f"Round-Trip-Time {address}: {(end_time - start_time) * 1000:.2f} ms\n")
        os.system("ping -c 1 " + address) # Ping an Worker senden

    except socket.timeout:
        print(f"Keine Antwort vom Worker {address} : {port} erhalten.\n")

    finally:
    # Socket schließen
        sock.close()


threads = []
# Worker-Adressen und Ports
worker_addresses = [('worker1', 12345), ('worker2', 12346), ('worker3', 12347)]
for worker in worker_addresses:
    thread = threading.Thread(target= send_healthcheck, args=(worker,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
