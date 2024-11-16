import socket
import os

def udp_worker():
    # Der Port wird aus der Umgebungsvariable WORKER_PORT gelesen
    port = int(os.getenv("WORKER_PORT", 12345))

    # Ein Socket wird erstellt und an den angegebenen Port gebunden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind(('0.0.0.0', port)) # Worker hört auf dem angegebenen Port

    print(f"Worker bereit, wartet auf Healthcheck-Anfragen auf Port {port} ...")
    running = True
    # Endlosschleife für den Worker
    while running:
        # UDP-Paket(data) empfangen und Adresse(addr) des Senders speichern
        # def recvfrom(self, bufsize: int, flags: int = ..., /) -> tuple[bytes, _RetAddress]: ...
        data, addr = sock.recvfrom(1024)

        # Wenn die empfangenen Daten 'healthcheck' sind, wird 'OK' zurückgesendet
        # def decode(self, encoding: str = "utf-8", errors: str = "strict") -> str: ...
        if data.decode() == 'healthcheck':
            
            print(f"Healthcheck-Anfrage von Controller mit Adresse {addr} erhalten auf Port {port}")

            #def sendto(self, data: ReadableBuffer, flags: int, address: _Address, /) -> int: ...
            sock.sendto(b'OK', addr) # Antwort an Controller senden

        # Wenn die empfangenen Daten 'stop' sind, wird die Endlosschleife beendet
        elif data.decode() == 'stop':
            print(f"Stop-Anfrage von Controller mit Adresse {addr} erhalten auf Port {port}")
            running = False

    # Socket schließen
    sock.close()

if __name__ == '__main__':
    udp_worker()
    