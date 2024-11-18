import socket
import time
import threading
import os
# from typing import List, Tuple

def send_healthcheck(worker_address: tuple, interval = 3):
    # Ein Socket wird erstellt und an einen beliebigen Port gebunden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # Timeout für die Antwort


    # Worker-Adresse und Port werden aus der Liste gelesen
    address, port = worker_address # Tuple unpacking
    i = 0 
    while i < 5:
        
        # Startzeit für die Round-Trip-Time
        start_time = time.time()
        print(f"Sende Healthcheck an {address} : {port} ...")

        sock.sendto(b'healthcheck', (address, port))  # Healthcheck senden

        try:
            data, _ = sock.recvfrom(1024)  # Antwort vom Worker empfangen

            # Endzeit für die Round-Trip-Time
            end_time = time.time()

            if data.decode() == 'OK':
                print(f"Antwort von Worker {address} -> {port} erhalten: OK")
            
            # Round-Trip-Time berechnen und ausgeben
            print(f"\nRound-Trip-Time {address}: {(end_time - start_time) * 1000:.2f} ms\n")
            #os.system("ping -c 1 " + address) # Ping an Worker senden

        except socket.timeout:
            print(f"Keine Antwort vom Worker {address} : {port} erhalten.\n")

        # Healthcheck alle 10 Sekunden
        i += 1
        time.sleep(interval) # 10 Sekunden warten für den nächsten Healthcheck

    sock.sendto(b'stop', (address, port))  # Worker stoppen
    # Socket schließen
    sock.close()

threads = []
# Worker-Adressen und Ports
worker_addresses = [('worker1', 12345), ('worker2', 12346), ('worker3', 12347)]


for worker in worker_addresses:
    thread = threading.Thread(target= send_healthcheck, args=(worker,))
    threads.append(thread)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
