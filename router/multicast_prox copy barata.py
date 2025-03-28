import json
import socket
import struct
import ipaddress
from subprocess import check_output
from multiprocessing import Process, Manager
import threading
import time

LOCAL_ADDRS = [x for x in check_output(['hostname', '-i']).decode().strip().split(' ')]
IP_RECVORIGDSTADDR = 20
RESERVED_ADDRS = ['127.0.0.1', '10.0.10.254', '10.0.11.254', '10.0.10.253', '10.0.11.253']
MIN_PORT = 10000
PROCESS_AMOUNT = 5

MULTICAST_GROUP = "224.0.0.1"  # Dirección de multicast

def proxy(port, servers, read_buffer=4196):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = (MULTICAST_GROUP, port)
    sock.bind(server_address)

    # Configuración para obtener la dirección de destino original
    sock.setsockopt(socket.IPPROTO_IP, IP_RECVORIGDSTADDR, 1)
    sock.setsockopt(socket.SOL_IP, socket.IP_TRANSPARENT, 1)

    print(f"Listening on {server_address}")

    while True:
        data, ancdata, _, address = sock.recvmsg(read_buffer, socket.MSG_CMSG_CLOEXEC)

        client_net = address[0].split('.')[2]
        primary_net = LOCAL_ADDRS[1].split('.')[2]
        # Evitar bucles y duplicados
        if address[0] in RESERVED_ADDRS or address[0] in LOCAL_ADDRS or client_net != primary_net:
            continue

        for cmsg_level, cmsg_type, cmsg_data in ancdata:
            if cmsg_level == socket.IPPROTO_IP and cmsg_type == IP_RECVORIGDSTADDR:
                family, port = struct.unpack('=HH', cmsg_data[0:4])
                port = socket.htons(port)

                if family != socket.AF_INET:
                    raise TypeError(f"Unsupported socket type '{family}'")

                ip = socket.inet_ntop(family, cmsg_data[4:8])
                print(f"Received data {data} from {address}")
                ip_object = ipaddress.ip_address(ip)

                if ip_object.is_multicast:
                    try:
                        message = json.loads(data.decode('utf-8'))
                        if message["message"] == "DISCOVER":
                            # Selecciona un servidor de la lista de servidores disponibles
                            if servers:
                                server_ip, server_ports = servers[0]  # Puedes implementar un algoritmo de selección más sofisticado
                                response = json.dumps({"message": "SERVER_ADDRESS", "ip": server_ip, "port": server_ports[1]})

                                # Crear un nuevo socket para enviar la respuesta multicast
                                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                    s.setsockopt(socket.SOL_IP, socket.IP_TRANSPARENT, 1)

                                    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)  
                                    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1) 
                                    s.setsockopt(
                                        socket.IPPROTO_IP,
                                        socket.IP_MULTICAST_IF,
                                        socket.inet_aton("192.168.1.100"),  
                                    )

                                    # Enviar la respuesta al cliente
                                    s.sendto(response.encode('utf-8'), address)
                                    print(f"Sent server address {server_ip}:{server_ports[1]} to {address}")
                            else:
                                print("No servers available to respond to client request")

                        elif message["message"] == "REGISTER":
                            # Registrar un servidor
                            server_ip = message["ip"]
                            server_ports = message["ports"]
                            servers.append((server_ip, server_ports))
                            print(f"Registered server {server_ip}:{server_ports}")
                            print(f"Current servers: {servers}")

                        elif message["message"] == "DISCOVER_NODE":
                            # Selecciona un servidor de la lista de servidores disponibles
                            if servers:
                                server_ip, server_ports = servers[0]  # Puedes implementar un algoritmo de selección más sofisticado
                                response = json.dumps({"message": "SERVER_ADDRESS", "ip": server_ip, "port": server_ports[0]})

                                # Crear un nuevo socket para enviar la respuesta multicast
                                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                    s.setsockopt(socket.SOL_IP, socket.IP_TRANSPARENT, 1)

                                    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)  
                                    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1) 
                                    s.setsockopt(
                                        socket.IPPROTO_IP,
                                        socket.IP_MULTICAST_IF,
                                        socket.inet_aton("192.168.1.100"),  
                                    )

                                    # Enviar la respuesta al servidor
                                    s.sendto(response.encode('utf-8'), (ip, port))
                                    print(f"Sent server address {server_ip}:{server_ports[0]} to {address}")
                    except json.JSONDecodeError:
                        print("Invalid JSON received")
                    except Exception as e:
                        print(f"Error handling request: {e}")

def check_servers_availability(servers):
    while True:
        time.sleep(30)
        for server in list(servers):  # Iterar sobre copia de la lista
            server_ip, server_ports = server
            try:
                # Usar UDP para heartbeats (más eficiente)
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.settimeout(5)  # Timeout más corto
                    sock.sendto(b"PING", (server_ip, server_ports[2]))
                    sock.recvfrom(1024)  # Esperar cualquier respuesta
                    print(f"Server {server_ip}:{server_ports[2]} responde")
            except (socket.timeout, ConnectionRefusedError, OSError):
                servers.remove(server)
                print(f"Server {server_ip}:{server_ports[2]} eliminado")

if __name__ == "__main__":
    with Manager() as manager:
        servers = manager.list()  # Lista compartida entre procesos para almacenar servidores
        processes = []

        # Iniciar el hilo de verificación de servidores
        heartbeat_thread = threading.Thread(target=check_servers_availability, args=(servers,))
        heartbeat_thread.daemon = True  # El hilo se detendrá cuando el proceso principal termine
        heartbeat_thread.start()

        for i in range(PROCESS_AMOUNT):
            p = Process(target=proxy, args=(MIN_PORT + i, servers))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()