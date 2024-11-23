import socket
import os

class UDPWorker:
    def __init__(self, port: int):
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

if __name__ == '__main__':
    port = int(os.getenv("WORKER_PORT", 12345))
    worker = UDPWorker(port)
    worker.start()