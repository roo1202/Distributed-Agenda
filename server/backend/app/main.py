import os
import sys

from chord import Address, ChordNode

def main():
    if len(sys.argv) < 6:
        print("Uso: python main.py <ip> <port1> <port2> <port3> <port4> <port5>")
        sys.exit(1)

    # Obtener la IP y los puertos de los argumentos de la línea de comandos
    ip = sys.argv[1]
    ports = sys.argv[2:7]  # Los puertos se pasan como argumentos

    # Crear una instancia de Address con la IP y los puertos
    address = Address(ip, ports)

    # Crear una instancia de ChordNode
    node = ChordNode(address, local=True)  

    # Mantener el servidor en ejecución
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Servidor detenido")

if __name__ == "__main__":
    main()