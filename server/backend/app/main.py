import os
import socket
import struct
import sys
import threading
import time
from contants import *

from chord import Address, ChordNode

def main():
    # Crear una instancia de ChordNode
    node = ChordNode()  

    #threading.Thread(target=multicast_listener(local_ip), daemon=True).start()

    # Mantener el servidor en ejecución
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Servidor detenido")



def multicast_listener(local_ip) -> None:
        """
        Function that listens for multicast requests.
        When it receives the DISCOVER_SERVER message, it responds with its IP address.
        """
        MCAST_GRP = "224.0.0.1"
        MCAST_PORT = 10003
        DISCOVER_MSG = "DISCOVER_SERVER"
        BUFFER_SIZE = 1024
        # Crear socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Permitir que varias instancias puedan reutilizar el puerto
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Vincular el socket a todas las interfaces en el puerto MCAST_PORT
        sock.bind(("", MCAST_PORT))

        # Unirse al grupo multicast
        mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(f"[Muticast] Escuchando mensajes en {MCAST_GRP}:{MCAST_PORT}")

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                message = data.decode().strip()
                print(f"Recibido mensaje: '{message}' desde {addr}")
                if message.startswith(DISCOVER_MSG + ":"):
                    _, rec_ip, rec_port = message.split(":")
                    print(f"{rec_ip} {rec_port}")
                    sock.sendto(local_ip.encode(), (rec_ip, int(rec_port)))
                else:
                    sock.sendto(local_ip.encode(), addr)
            except Exception as e:
                print(f"Error en el listener: {e}")
                time.sleep(1)


if __name__ == "__main__":
    main()