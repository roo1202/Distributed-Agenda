
import hashlib
import json
import os
import shutil
import socket
import struct
import threading
import time
import zipfile
from models.db_model import DBModel, notify_data
from contants import *
import struct

def hash_key(key: str) -> int:
    """
    Función de hash que calcula el hash SHA-1 de una cadena de caracteres y devuelve un número entero que se utiliza como la clave del nodo en la red Chord.
    """
    sha1 = hashlib.sha1(key.encode('utf-8'))
    hash_value = int(sha1.hexdigest(), 16) 
    return hash_value


class Address():
    def __init__(self,ip,ports):
        self.ip = ip
        self.ports = ports

    def __str__(self):
        return f"tcp:{self.ip}:{self.ports[0]}"
    
    def __repr__(self):
        return f"ip:{self.ip} ports:{self.ports}"


def convert_into_int(bytes_seq):
    # decodifica los bytes en un entero con orden de byte 'big'
    return int.from_bytes(bytes_seq, byteorder='big')

def create_zip(zip_name,files_names):
    # Crea un archivo ZIP llamado "datos.zip"
    with zipfile.ZipFile(zip_name , "w") as mi_zip:
    # Agrega subarchivos al archivo ZIP
        for file in files_names:
          mi_zip.write(file)

def create_json_file(data,file_name):
    json_data = json.dumps(data)

    # Escribe la cadena JSON en un archivo llamado "datos.json"
    with open(file_name, "w") as f:
      f.write(json_data)

#region ChordNode
class ChordNode:
    def __init__(self):

        self.address=Address(socket.gethostbyname(socket.gethostname()), [CLIENT_PORT, SERVER_PORT, FILES_PORT, CHECK_PORT])
        print(f'Iniciando nodo chord con ip: {self.address.ip}')
        self.leader = None
        self.nodeSet = []                           # Nodes discovered so far
        self.time_nodes = {}
        self.database = {}
        self.joined = False

        #Setting node ID
        self.nodeID = hash_key(self.address.ip) 
        self.nodeSet.append(self.nodeID)
        self.db = DBModel(self.nodeID)
        self.db.create_user({"user_name": 'roger',
                             "user_email": 'fuentesroger65@gmail.com',
                             "password":'1234'})
        self.nBits = 160
        self.Sucessors = [None,None]
        
       
        #Initializing Finger Table
        self.FT = [None for i in range(self.nBits+1)]

        self.MAXPROC = pow(2,160)
        self.node_address = {}

        #print(socket.gethostbyname(socket.gethostname()))

        #initializing sockets
        
        #Cuando otro nodo de la red quiera saber si este nodo esta, debe conectarse a este socket o 
        # si este nodo es el lider el resto se conecta a este socket para actualizar su lista de nodos
        
        self.discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.discover.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.discover.bind((HOST, SERVER_PORT))
        self.discover.listen()

        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind((HOST, CLIENT_PORT))
        self.receiver.listen()

        #Puerto para recibir archivos
        self.file_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.file_receiver.bind((HOST, FILES_PORT))
        self.file_receiver.listen()

        #Puerto para chequeos
        # self.check_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.check_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.check_receiver.bind((HOST, CHECK_PORT))
        # self.check_receiver.listen()

        
        # Registrar el servidor en el router multicast
        #self.register_with_multicast_router()

        # Iniciar los hilos para mandar y manejar heartbeats
        self.heartbeat_thread = threading.Thread(target=self.announce_availability)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        self.heartbeat_listener = threading.Thread(target=self.listen_heartbeats)
        self.heartbeat_listener.daemon=True
        self.heartbeat_listener.start()
        print('Escuchando servidores disponibles')

        time.sleep(5)
        self.join()

        # Hilo para limpiar nodos
        self.cleanup_nodes_thread = threading.Thread(target=self.cleanup_nodes)
        self.cleanup_nodes_thread.daemon =True
        self.cleanup_nodes_thread.start()

        # Hilo para el movimiento de la base de datos
        self.discover_resp_thread = threading.Thread(target=self.get_discover_request)
        self.discover_resp_thread.daemon = True
        self.discover_resp_thread.start()

        self.run()

        
    #region send_request
    def send_request(self, address,data=None,answer_requiered=False,expected_zip_file=False,num_bytes=1024):     
                sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try : 
                    sender.connect(address)
                except ConnectionRefusedError as e :
                    sender.close()
                    return None
                    #print("Error de conexion :", e)
                    
                # establecer un tiempo de espera de 10 segundos
                print(f'mandando mensaje a {address} con data {data}')
                sender.settimeout(10)
                if data is not None :
                    json_data = json.dumps(data).encode('utf-8')
                    sender.send(json_data)
                else: 
                    self.send_copy_db(sender,num_bytes)

                if answer_requiered:
                    try:
                        # Esperar la llegada de un mensaje
                        
                        if not expected_zip_file:
                            data = sender.recv(num_bytes)
                            data = data.decode('utf-8')
                            data = json.loads(data) 
                            print(f'data recibida {data}')
                            sender.close()
                        else:
                            data = self.recieve_copy_db(sender,num_bytes)
                    except socket.timeout:
                        # Manejar la excepción si se agotó el tiempo de espera
                        if not expected_zip_file or not data: notify_data("Tiempo de espera agotado para recibir un mensaje","Error")
                sender.close()
                return data 

    #region send_copy_db
    def send_copy_db(self, conn, num_bytes=4096):
        try:
            file_size = os.path.getsize(f"copia{self.nodeID}.db")
            print(f'enviando un archivo de {file_size} bytes')
            
            # Enviar el tamaño del archivo (usamos struct para empaquetar el número)
            conn.sendall(struct.pack("!Q", file_size))

            with open(f"copia{self.nodeID}.db", "rb") as f:
                while True:
                    l = f.read(num_bytes)
                    if not l:
                        break  # Fin del archivo
                    conn.sendall(l)  # Envía todos los datos

            print("Base de datos enviada correctamente.")
            return True

        except Exception as e:
            print(f"Error al enviar copia.db: {e}")
            return False

    #region recieve_copy_db
    def recieve_copy_db(self, conn, num_bytes=4096):
        try:
            # Recibir el tamaño del archivo
            file_size_data = conn.recv(8)  # 8 bytes para un entero de 64 bits
            file_size = struct.unpack("!Q", file_size_data)[0]
            print(f'recibiendo un archivo de {file_size} bytes')

            with open(f"copia{self.nodeID}.db", 'wb') as f:
                print('escribiendo copia.db')
                remaining_bytes = file_size
                while remaining_bytes > 0:
                    l = conn.recv(min(num_bytes, remaining_bytes))
                    if not l:
                        break  # Conexión cerrada
                    f.write(l)
                    remaining_bytes -= len(l)

            print("Base de datos recibida correctamente.")
            return True

        except Exception as e:
            print(f"Error al recibir copia.db: {e}")
            return False

        
    @property
    def Predecessor(self):
        return self.FT[0]
    
    @property 
    def Req_Method(self):
        return { CREATE_PROFILE: self.db.create_user ,REP_PROFILE: self.db.create_user , 
                CREATE_GROUP: self.db.create_group, REP_GROUP:self.db.create_group, 
                CREATE_EVENT: self.db.create_event, REP_EVENT: self.db.create_event, 
                ACCEPT_EVENT: self.db.accept_pendient_event,ACCEPT_EVENT_REP:self.db.accept_pendient_event, 
                ADD_MEMBER_GROUP:self.db.add_user_to_group, ADD_MEMBER_GROUP_REP:self.db.add_user_to_group,
                DELETE_EVENT: self.db.delete_event, DELETE_EVENT_REP: self.db.delete_event,
                DELETE_NOTIFICATION:self.db.delete_notification,DELETE_NOTIFICATION_REP:self.db.delete_notification, 
                GET_PROFILE: self.db.get_user_by_id,
                GET_NOTIFICATIONS: self.db.get_notifications,
                GET_EVENTS: self.db.get_events,
                GET_HIERARCHICAL_MEMBERS: self.db.get_hierarchy_level,
                GET_GROUP_TYPE:self.db.is_hierarchy_group,
                GET_GROUPS: self.db.get_groups, 
                GET_EVENT:self.db.get_event_by_id
                }
    

    @property
    def Serialize_Address(self):
        return { node : (address.ip,address.ports) for node,address in self.node_address.items()}
    
    #region announce_availability
    def announce_availability(self, multicast_group= MCAST_GRP, multicast_port= MCAST_PORT):
        print("Announcing availability")
        message = f"AVAILABLE:{self.nodeID}:{self.address.ip}:{self.address.ports}"
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
                s.sendto(message.encode(), (multicast_group, multicast_port))
            time.sleep(5)

    #region register_with_router
    def register_with_multicast_router(self):
        multicast_group = "224.0.0.1"
        multicast_port = 10000

        # Crear un mensaje de registro
        register_message = {
            "message": "REGISTER",
            "ip": self.address.ip,
            "ports": (SERVER_PORT, CLIENT_PORT, HEARD_PORT)  
        }

        # Enviar el mensaje al router multicast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        sock.sendto(json.dumps(register_message).encode('utf-8'), (multicast_group, multicast_port))
        print(f"Registered with multicast router: {self.address.ip}:{self.address.ports[0]}")
        sock.close()

    #region handle_heartbeat
    def handle_heartbeat(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as hb_socket:
            hb_socket.bind((HOST, HEARD_PORT))
            while True:
                data, addr = hb_socket.recvfrom(1024)
                if data == b"PING":
                    hb_socket.sendto(b"PONG", addr)  # Respuesta simple

    def inbetween(self, key, lwb, upb):                                         
        if lwb <= upb:                                                            
            return lwb <= key < upb                                                                                                         
        return (lwb <= key and key < upb + self.MAXPROC) or (lwb <= key + self.MAXPROC and key < upb)                        

    def finger(self, i):
        succ = (self.nodeID + pow(2, i-1)) % self.MAXPROC    # succ(p+2^(i-1))
        lwbi = self.nodeSet.index(self.nodeID)               # own index in nodeset
        upbi = (lwbi + 1) % len(self.nodeSet)                # index next neighbor
        for _ in range(len(self.nodeSet)):                   # go through all segments
            if self.inbetween(succ, self.nodeSet[lwbi]+1, self.nodeSet[upbi]+1):
                return self.nodeSet[upbi]                        # found Sucessor
            (lwbi,upbi) = (upbi, (upbi+1) % len(self.nodeSet)) # go to next segment
        return None                                                                
    
    #region recompute_finger_table
    def recomputeFingerTable(self,write_to_new_suc = False):
        if len(self.nodeSet) > 1:
            self.nodeSet.sort()
            self.FT[0]  = self.nodeSet[self.nodeSet.index(self.nodeID)-1] # Predecessor
            self.FT[1:] = [self.finger(i) for i in range(1,self.nBits+1)] # Sucessors
        elif len(self.nodeSet)  == 1:
            self.FT = [self.nodeSet[0] for _ in range(1,self.nBits+1)]
        if not self.Sucessors[0]: 
            self.Sucessors[0] = self.FT[1] 
            if len(self.nodeSet) > 2 :
                self.Sucessors[1] = self.FT[2]
            return 
        if write_to_new_suc and len(self.nodeSet) > 2 and self.Sucessors[0] != self.nodeID and self.Sucessors[1] != self.nodeID and (self.Sucessors[0] != self.FT[1] or self.Sucessors[1] != self.FT[2]):
            self.Sucessors[0] = self.FT[1]
            self.Sucessors[1] = self.FT[2]
            self.send_data_to_sucessors()

    def printFT(self):
        print('FingerTable:')
        for row in self.FT:
            print(row)


    def localSuccNode(self, key): 
        if self.inbetween(key, self.FT[0]+1, self.nodeID+1): # key in (FT[0],self]
            return self.nodeID                                 # node is responsible
        elif self.inbetween(key, self.nodeID+1, self.FT[1]): # key in (self,FT[1]]
            return self.FT[1]                                  # Sucessor responsible
        for i in range(1, self.nBits+1):                     # go through rest of FT
            if self.inbetween(key, self.FT[i], self.FT[(i+1) % self.nBits]):
                return self.FT[i]                                # key in [FT[i],FT[i+1])
    
    def get_addresses(self,addresses):
        return {int(node):Address(address[0],address[1]) for node,address in addresses.items()}

    #region recieve_checks
    def recieve_checks(self):
        while True:
            conn, addr = self.check_receiver.accept()
            # conn es otro socket que representa la conexion 
            msg=conn.recv(1024)
            msg = msg.decode('utf-8')
            msg = json.loads(msg)         
            request = msg["message"]
            print(f'Recibido {msg} desde {addr}')

            #someone wants to contact me to join to the network
            if request == JOIN_REQ:   
                data = {"message": JOIN_REP, "ip": self.address.ip , "ports": self.address.ports , "nodeID": self.nodeID, "leader": self.leader}
                newID = msg["nodeID"]
                if not newID in self.nodeSet:
                    notify_data(f"Receiving JOIN request from {newID}","Join")

                    #if Im the leader 
                    if self.leader == self.nodeID:
                        self.nodeSet.append(newID)
                        self.nodeSet.sort()
                        self.recomputeFingerTable()
                        self.node_address[newID] = Address(msg["ip"],msg["ports"])
                        data["nodes_ID"] = self.nodeSet                
                        data["addresses"] = self.Serialize_Address
                    json_data = json.dumps(data).encode('utf-8')
                    notify_data("Sending JOIN_RESP","Join")
                    conn.send(json_data)

            #Someone wants to check if Im alive
            if request == CHECK_REQ:
                data = {"message": CHECK_REP,"ip": self.address.ip , "ports": self.address.ports , "nodeID": self.nodeID, "leader": self.leader, "nodes_ID":self.nodeSet, "addresses":self.Serialize_Address }
                newID = msg["nodeID"]

                notify_data(f"Receiving CHECK request from {newID}","Check")
                if  self.leader == self.nodeID and msg["leader"] == newID  and newID > self.nodeID:                    
                    self.leader = newID
                json_data = json.dumps(data).encode('utf-8')
                conn.send(json_data)

            if request == CHECK_SUC:
                    id = msg["nodeID"]
                    notify_data(f'Recieving CHECK_SUC request from {id}',"Check")
                    data = {"message": CHECK_SUC_RESP,"ip": self.address.ip , "ports": self.address.ports , "nodeID": self.nodeID, "leader": self.leader }
                    notify_data(f'Sending CHECK_SUC_RESP request to {id}',"Check")
                    json_data = json.dumps(data).encode('utf-8')
                    conn.send(json_data)

    #region get_discover_request
    def get_discover_request(self):
        while True:
            conn, addr = self.discover.accept()
            # conn es otro socket que representa la conexion 
            msg=conn.recv(1024)
            msg = msg.decode('utf-8')
            msg = json.loads(msg) 
            
            request = msg["message"]
    
            # I have a new predeccesor (sucessor)
            if request == MOV_DATA_REQ or request == REP_DATA_REQ:
                get_data =  request == MOV_DATA_REQ
                action = "MOV_DATA_REQ" if get_data else "REP_DATA_REQ"
                response =   "MOV_DATA_REP" if get_data else "REP_DATA_REP"
                node = msg["nodeID"]
                notify_data(f"Receiving {action} from {node}","GetData")
                self.index_data(msg)                  
                self.send_copy_db(conn)
                notify_data(f"Sending {response} to {node}","GetData")
                if not get_data and len(self.nodeSet) > 2: 
                    if self.Sucessors[0] > msg["nodeID"]:
                        self.Sucessors[1] = self.Sucessors[0]
                        self.Sucessors[0] = msg["nodeID"]
                        self.node_address[self.Sucessors[0]] = Address(msg["ip"],msg["port"])
                    else:
                        self.Sucessors[1]= msg["nodeID"]
                        self.node_address[self.Sucessors[1]] = Address(msg["ip"],msg["port"])
                # elif len(self.nodeSet) > 3: 
                #     self.delete_rep_data(msg)  

            # if request == GET_NODES:
            #     id = msg["nodeID"]
            #     notify_data(f'Recieving GET_NODES request from {id}',"GetData")
            #     addresses = self.Serialize_Address
            #     data = {"message": SET_NODES,"ip": self.address.ip , "ports": self.address.ports , "nodeID": self.nodeID, "nodeSet":self.nodeSet, "addresses":addresses}
            #     data = json.dumps(data).encode('utf-8')
            #     conn.send(data)

            # if request == SET_LEADER:
            #     id = msg["nodeID"]
            #     notify_data(f'Recieving SET_LEADER request from {id}',"Check")
            #     addresses,self.nodeSet = self.discover_nodes(True)
            #     self.node_address = self.get_addresses(addresses) 
            #     self.recomputeFingerTable(write_to_new_suc = True)       

            if request == DEL_REP_DATA:
                id = msg["nodeID"]
                notify_data(f"Receiving DEL_REP_DATA from {id}",'database')
                self.delete_rep_data(msg)

    def index_data(self,msg=None):
        start_index = self.Predecessor
        end_index = self.nodeID
        if msg:  
            start_index = msg["startID"] 
            end_index =   msg["endID"] 
        #print(start_index,end_index)
        condition = lambda id : self.inbetween(int(id),start_index,end_index)
        self.db.get_filtered_db(condition,f'copia{self.nodeID}.db')

    def delete_rep_data(self,msg):
        start_index = msg["startID"]
        end_index =  msg["endID"]
        print(start_index,end_index)
        condition = lambda id : self.inbetween(int(id),start_index,end_index)
        self.db.delete_replicated_db(condition)

    def recieve_files(self):
        while True:          
            conn, addr = self.file_receiver.accept()
            notify_data(f"Receiving file from {addr}",'database')
            self.recieve_copy_db(conn,8192)
            self.db.replicate_db(f'copia{self.nodeID}.db')
            notify_data(f"Replicating data","database")
            self.db.check_db()
            os.remove(f'copia{self.nodeID}.db')

    #region get nodes
    def get_nodes(self):           
            data = {"message": GET_NODES, "ip": self.address.ip , "ports": self.address.ports, "nodeID": self.nodeID}
            leader_address = self.node_address[self.leader] 
            data = self.send_request((leader_address.ip,SERVER_PORT),data=data,answer_requiered=True)
            if data:
              if data["message"] == SET_NODES:
                self.nodeSet = data["nodeSet"]
                notify_data(f"Upadating node set :{self.nodeSet}","GetData")
                self.node_address = self.get_addresses(data["addresses"])
                print(self.node_address)
                self.recomputeFingerTable(write_to_new_suc = True)
              else:
                msg = data["message"]
                notify_data(f"Not expected {msg} !!!!!!!!!!!!!!!!","Error")
            else:
                addresses,self.nodeSet = self.discover_nodes(True)
                #building node_address dict
                self.node_address = self.get_addresses(addresses)       
                #Computing Finger Table
                self.recomputeFingerTable(write_to_new_suc = True)

    #region check_sucessors
    # def check_sucessors(self):
    #     while True:
    #       time.sleep(20)
    #       for sucessor in self.Sucessors:
    #         if sucessor and sucessor != self.nodeID:
    #             data = {"message": CHECK_SUC, "ip": self.address.ip , "ports": self.address.ports, "nodeID": self.nodeID, "leader":self.leader,"nodeSet":self.nodeSet}
    #             address = (self.node_address[sucessor].ip,CHECK_PORT)
    #             notify_data(f"Sending CHECK_SUC to {sucessor}","Check")
    #             data = send_request(address,data=data,answer_requiered=True)
    #             notify_data(f'Recieving CHECK_SUC_RESP' ,"Check")
    #             if not (data or self.leader == self.nodeID): 
    #                 self.get_nodes()  

    def check_sucessors(self):
        while True:
            time.sleep(20)
            for i,sucessor in enumerate(self.Sucessors):
                if sucessor is not None and sucessor != self.nodeID and sucessor != self.nodeSet[(self.nodeSet.index(self.nodeID) + i + 1) % len(self.nodeSet)] :
                    self.recomputeFingerTable(write_to_new_suc = True)
                    self.printFT()

                    
    def send_data_to_sucessors(self):
        notify_data(f"New sucessors found {self.Sucessors[0]}, {self.Sucessors[1]}","Join")
        self.index_data(False)
        for sucessor in self.Sucessors:
            address = (self.node_address[sucessor].ip,FILES_PORT)
            if sucessor != self.nodeID:
                self.send_request(address,num_bytes=5120)
                notify_data(f"Sending REP_DATA to {sucessor}","GetData")       
    
    #region leader_labor
    def leader_labor(self):
        time.sleep(30)
        while self.leader == self.nodeID and len(self.nodeSet) > 1: 
            addresses , new_nodes = self.check_network()

            if  len(new_nodes) > 1 and not (new_nodes == self.nodeSet):
                self.node_address = self.get_addresses(addresses)
                self.nodeSet = new_nodes
                notify_data(f"New nodes {self.node_address}","Join")
                self.recomputeFingerTable(write_to_new_suc = True)
            else: 
                notify_data(f"Nodes set already update","Check")
                notify_data(f"Nodes {self.node_address}","Join")
            time.sleep(30)

#region listen_heartbeats
    def listen_heartbeats(self):
        """Escucha mensajes multicast de otros servidores."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((MCAST_GRP, MCAST_PORT))
            s.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0"),
            )
            while True:
                data, _ = s.recvfrom(4096)
                message = data.decode()
                if message.startswith("AVAILABLE"):
                    _, node_id, ip, ports = message.split(":")
                    node_id = int(node_id)
                    if node_id not in self.nodeSet:
                        self.joined = True
                        self.nodeSet.append(node_id)
                        self.node_address[node_id] = Address(ip, ports.split(","))
                    self.time_nodes[node_id] = time.time()


    def cleanup_nodes(self):
        """Elimina nodos inactivos de la lista."""
        while True:
            current_time = time.time()
            to_remove = [
                node_id
                for node_id, last_seen in self.time_nodes.items()
                if current_time - last_seen > NODE_TIMEOUT
            ]
            for node_id in to_remove:
                self.nodeSet.remove(node_id)
                del self.time_nodes[node_id]
            time.sleep(10)

    #region check_network
    def check_network(self):
        discovered_nodes = [self.nodeID]
        discovered_addresses = {self.nodeID:(self.address.ip,self.address.ports)}
        
        for _,address in self.node_address.items():
            if address.ip != self.address.ip:
                #print(f'Connecting to {address} to check if node is alive') 
                data = {"message": CHECK_REQ, "ip": self.address.ip , "ports": self.address.ports, "nodeID": self.nodeID,"leader":self.nodeID}
                data = self.send_request((address.ip, CHECK_PORT),data=data,answer_requiered=True)
                if data:
                    if data["message"] == CHECK_REP:
                        current_id = data["nodeID"]
                        leader = data["leader"]
                        ip = data["ip"]
                        ports = data["ports"]
                        discovered_addresses[current_id] = (ip,ports)
                        discovered_nodes.append(current_id)

                        notify_data(f"Check response received from {current_id}","Check")

                        if leader == current_id and current_id > self.nodeID:
                            notify_data(f'There is a Leader with ID {current_id}, greater than mine. Im not leader anymore',"Join")
                            self.leader = current_id
                            return data["addresses"],data["nodes_ID"]
        discovered_nodes.sort()
        return discovered_addresses, discovered_nodes

    #region run
    def run(self):
        #Receiving requests
        while True:
            print("next_step")
            print(f"My address: {str(self.address)}")
            conn, addr = self.receiver.accept()
            msg=conn.recv(1024)
            msg = msg.decode('utf-8')
            data = json.loads(msg) 
            print(f">>>>> {data}")

            #unpacking data
            request = data["message"]
           
            if request == STOP: 
                break
            elif request in self.Req_Method.keys():
                notify_data(f"Receiving {request} from {addr}","SetData")
                if 30 <= int(request) < 60:  
                    if int(request)%2 == 0 :
                        self.update_key(data,request,addr)
                    else: 
                        self.Req_Method[request](data)
                        self.db.check_db()
                if 60 <= int(request) < 80:
                   self.get_key(data,request)

            elif request == LOOKUP_REQ: 
            #   if not self.leader == self.nodeID:
            #     self.get_nodes()                  
                self.lookup_key(data)               

            elif request == SET_DATA_REQ:
               p = data["port"]
               print(self.address.ports[0])
               notify_data(f"Receiving SET_DATA_REQ from {p}","GetData")                
               self.update_key(data) 

            elif request == GET_DATA_REQ:
               notify_data(f"Receiving GET_DATA_REQ","GetData")
               self.get_key(data,addr)

    #region lookup_key   
    def lookup_key(self,data):
                key = data["key"]
                ip = data["ip"]
                port = data["port"]
            
                notify_data(f"Receiving LOOKUP_REQ of {key} key","GetData")
                #print(self.FT)
                nextID = self.localSuccNode(key)          # look up next node #-
                
                if not nextID == self.nodeID :
                    #notify_data(f"Connecting to {nextID}","GetData")
                    data = {"message": LOOKUP_REQ, "ip": ip , "port": port, "key": key} # send to succ
                    self.send_request((self.node_address[nextID].ip,CLIENT_PORT),data=data)
                    notify_data(f"Sending LOOKUP_REQ to {nextID} node ","Get_Data")
                else:
                    data = {"message": LOOKUP_REP, "ip": self.address.ip , "port": CLIENT_PORT, "node":  nextID,"key":key}        
                    self.send_request((ip,int(port)),data=data)               

    def update_key(self,data,request,addr):
                key = data["user_key"]
                nextID = self.localSuccNode(key)          # look up next node #-
                
                if not nextID == self.nodeID :
                    #data = {"message": request, "ip": ip , "port": self.address.ports[0], "user_key": key } # send to succ                    
                    notify_data(f"Sending {request}  to {nextID}: {str(self.node_address[nextID])} node ","SetData")
                    self.send_request((self.node_address[nextID].ip,CLIENT_PORT),data=data)
                else :
                    self.Req_Method[request](data)
                    self.db.check_db()
                    for sucessor in self.Sucessors:
                        if sucessor != self.nodeID:
                            notify_data(f"Sending {int(request)+1} to {sucessor}","SetData")
                            #data = {"message": str(int(request)+1), "ip": self.address.ip , "port": self.address.ports[0], "node":  nextID,"user_key":key}
                            data["message"] = str(int(request)+1)
                            self.send_request((self.node_address[sucessor].ip,CLIENT_PORT),data=data)


    def get_key(self,data,request):            
                key = data["user_key"]
                sender_addr = data["sender_addr"]
                nextID = self.localSuccNode(key)          # look up next node #-
                if not nextID == self.nodeID :
                    #data = {"message": request, "ip": ip , "port": port, "key": key,"sender_addr":sender_addr } # send to succ 
                    self.send_request((self.node_address[nextID].ip,CLIENT_PORT),data=data)
                    notify_data(f"Sending {request} to {nextID} node : {str(self.node_address[nextID])} ","GetData")
                else:
                    data = self.Req_Method[request](data)
                    #data = self.get_data(data)
                    notify_data(f"Sending  {int(request)+1} to {sender_addr}","GetData")
                    self.send_request((sender_addr[0],sender_addr[1]),data=data)
                    
    def set_data(self,data):
        key = data["key"]
        value = data["value"]
        self.database[key] = value
        notify_data(f"Set {value} to {key} key","SetData")

    def get_data(self,data):
        key = data["key"]
        try: value = self.database[key] 
        except KeyError:
           notify_data(f"Key {key} not found","Error")
           return None
        notify_data(f"Obtained {value} to {key} key","GetData")
        return value      

    #region join
    def join(self):

        # addresses,self.nodeSet = self.discover_nodes(False)
        # notify_data("Discovered nodes %s" % (self.nodeSet),"Join"
        #building node_address dict
        #self.node_address = self.get_addresses(addresses)

        print(f'Uniendome a una red de {len(self.nodeSet) - 1} servidores')
        #Computing Finger Table
        self.recomputeFingerTable()

        if len(self.nodeSet) > 3:
            try:
                self.update_data(True)
            except :
                print('No se pudieron obtener los datos necesarios')
            self.conn_to_suc_suc()
        elif len(self.nodeSet) > 1 :
            notify_data(f"Connecting to node {self.Sucessors[0]}","GetData")
            address = (self.node_address[self.Sucessors[0]].ip,SERVER_PORT)
            data = {"nodeID":self.nodeID,
                    "message": REP_DATA_REQ,
                    "startID": 0,
                    "endID": self.MAXPROC,
                    "ip": self.address.ip,
                    "port": self.address.ports[1]}
            response = self.send_request(address, data, answer_requiered=True, expected_zip_file=True, num_bytes=5120)
            if response:
                self.initialize_data(f'copia{self.nodeID}.db')
                notify_data(f"Data updated","database")
                self.db.check_db()
                os.remove(f'copia{self.nodeID}.db')
        else:
            print("[+] Primer nodo del anillo.")
            self.joined = True
            return

        self.recieve_files_thread =  threading.Thread(target=self.recieve_files)
        self.recieve_files_thread.daemon = True
        self.recieve_files_thread.start()

        self.check_sucessors_thread = threading.Thread(target=self.check_sucessors)
        self.check_sucessors_thread.daemon = True
        self.check_sucessors_thread.start()

    #region discover_servers
    def discover_servers(self, timeout: int = 5) -> list:
        """
        Descubre servidores disponibles en la red multicast
        :param timeout: Tiempo máximo de espera en segundos
        :return: Lista de tuplas (ip, puertos) de servidores encontrados
        """
        MCAST_GRP = "224.0.0.1"
        MCAST_PORT = 10003
        BUFFER_SIZE = 1024

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # Configuración básica del socket
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(timeout)
                
                # Configuración multicast
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, 
                            socket.inet_aton(MCAST_GRP) + socket.inet_aton('0.0.0.0'))

                # Enviar solicitud de descubrimiento
                sock.sendto(json.dumps({"message": "DISCOVER_NODE"}).encode(), (MCAST_GRP, MCAST_PORT))
                
                servers = []
                start = time.time()
                
                while time.time() - start < timeout:
                    print('entrando en while')
                    try:
                        data, addr = sock.recvfrom(BUFFER_SIZE)
                        print(data)
                        print(data.decode())
                        response = json.loads(data.decode('utf-8'))
                        print(response)
                        if response["message"] == "SERVER_ADDRESS":
                            print('recibido server address')
                            server_info = (response["ip"], response["port"])
                            print(server_info)
                            if server_info not in servers:
                                servers.append(server_info)
                                print(f"Servidor descubierto: {response['ip']}:{response['port']}")
                    except (socket.timeout, json.JSONDecodeError, KeyError):
                        continue
                    except Exception as e:
                        print(f"Error en recepción: {str(e)}")
                        break

                return servers
                
        except Exception as e:
            print(f"Error en descubrimiento: {str(e)}")
            return []

    #region discover_nodes
    def discover_nodes(self,find_leader):
        current_leader = self.nodeID
        leader_address = self.address
        discovered_nodes = [self.nodeID]
        discovered_addresses = {self.nodeID:(self.address.ip,self.address.ports)}
        msg_to_send = CHECK_REQ if find_leader else JOIN_REQ
        msg_to_rcv  = CHECK_REP if find_leader else JOIN_REP
        possible_addresses = []
        if not find_leader:
            servers = self.discover_servers()
            print(servers)
            if len(servers) > 0 :
                s1 = servers[0]
                print(f's1[0]: {s1[0]}')
                print(f's1[1]: {s1[1]}')
                possible_addresses = [Address(s1[0], [CHECK_PORT])] 
        else :
            possible_addresses = [address for _, address in self.node_address.items()]
        for address in possible_addresses:
            data = {"message": msg_to_send, "ip": self.address.ip , "ports": self.address.ports, "nodeID": self.nodeID, "leader":self.leader,"nodeSet":self.nodeSet}
            data = self.send_request((address.ip, int(CHECK_PORT)),data=data,answer_requiered=True)
            if data:
                if data["message"] == msg_to_rcv:
                    current_id = data["nodeID"]
                    leader = data["leader"]
                    ip = data["ip"]
                    ports = data["ports"]
                    discovered_addresses[current_id] = (ip,ports)
                    discovered_nodes.append(current_id)

                    notify_data(f'Node {current_id} discovered',"Join")

                    if leader == current_id:
                        self.leader = current_id
                        notify_data(f'Leader found at node {current_id}',"Join")
                        return data["addresses"],data["nodes_ID"]
                
                    elif current_id > current_leader:
                        current_leader = current_id
                        leader_address = Address(ip,ports)
                                   
        if current_leader == self.nodeID:
                notify_data('Setting myself as leader',"Join")
                discovered_nodes.sort()
                self.leader = self.nodeID
                thread = threading.Thread(target=self.leader_labor)
                thread .start()
        else: 
            notify_data(f'Greatest node found : {current_leader}. That one is the leader',"Join")
            data = {"message": SET_LEADER, "ip": self.address.ip, "ports": self.address.ports, "nodeID": self.nodeID, "leader":self.leader,"nodeSet":self.nodeSet}
            self.send_request((leader_address.ip,SERVER_PORT),data=data)
            discovered_nodes.sort()
            self.leader = current_leader

        return discovered_addresses,discovered_nodes   
    
    #region update_data
    def update_data(self,get_data):
        my_index = self.nodeSet.index(self.nodeID)

        node1 = self.Sucessors[0] if get_data else self.Predecessor
        node2 = self.Sucessors[1] if get_data else self.nodeSet[(my_index-2)%len(self.nodeSet)] 
        request = MOV_DATA_REQ if get_data else REP_DATA_REQ
        response = MOV_DATA_REP if get_data else REP_DATA_REP
        receiver = "sucessor" if get_data else "predecessor"
        update_method = self.initialize_data if get_data else self.db.replicate_db
        
        if get_data:
            # Copiando los datos que me corresponden desde mi sucesor
            notify_data(f"Connecting to {receiver} : node {node1}","GetData")
            address = (self.node_address[node1].ip,SERVER_PORT)
            data = {"message": REP_DATA_REQ, "ip": self.address.ip , "port": self.address.ports, "nodeID": self.nodeID}
            data["startID"] = self.Predecessor 
            data["endID"] = self.nodeID
            successfull = self.send_request(address,data=data,answer_requiered=True,expected_zip_file=True,num_bytes=5120)
            if successfull:
                update_method(f'copia{self.nodeID}.db')
                notify_data(f"Data updated","database")
                self.db.check_db()
                os.remove(f'copia{self.nodeID}.db')

        # Moviendo los datos correspondientes a mi segundo predecesor (desde mi primer sucesor)
        notify_data(f"Connecting to {receiver} : node {node1}","GetData")
        address = (self.node_address[node1].ip,SERVER_PORT)
        data = {"message": request, "ip": self.address.ip , "port": self.address.ports, "nodeID": self.nodeID}
        data["startID"] = self.nodeSet[(my_index-3)%len(self.nodeSet)] 
        data["endID"] = self.nodeSet[(my_index-2)%len(self.nodeSet)] 
        successfull = self.send_request(address,data=data,answer_requiered=True,expected_zip_file=True,num_bytes=5120)
        if successfull:
            self.db.replicate_db(f'copia{self.nodeID}.db')
            notify_data(f"Data updated","database")
            self.db.check_db()
            os.remove(f'copia{self.nodeID}.db')

        # Moviendo los datos correspondientes a mi predecesor (desde mi segundo sucesor)
        notify_data(f"Connecting to {receiver} : node {node2}","GetData")
        address = (self.node_address[node2].ip,SERVER_PORT)
        data = {"message": request, "ip": self.address.ip , "port": self.address.ports, "nodeID": self.nodeID}
        data["startID"] = self.nodeSet[(my_index-2)%len(self.nodeSet)] 
        data["endID"] = self.nodeSet[(my_index-1)%len(self.nodeSet)] 
        successfull = self.send_request(address,data=data,answer_requiered=True,expected_zip_file=True,num_bytes=5120)
        if successfull:
            self.db.replicate_db(f'copia{self.nodeID}.db')
            notify_data(f"Data updated","database")
            self.db.check_db()
            os.remove(f'copia{self.nodeID}.db')

        return True

    def conn_to_suc_suc(self):
        my_index = self.nodeSet.index(self.nodeID)
        s1 = self.nodeSet[(my_index+1)%len(self.nodeSet)] 
        s2 = self.nodeSet[(my_index+2)%len(self.nodeSet)] 
        p1 = self.nodeSet[(my_index-1)%len(self.nodeSet)] 
        p2 = self.nodeSet[(my_index-2)%len(self.nodeSet)] 
        p3 = self.nodeSet[(my_index-3)%len(self.nodeSet)] 
        address1 = (self.node_address[s1].ip,SERVER_PORT)
        notify_data(f"Sending DEL_REP_DATA to sucessor : node {s1}","GetData")
        data = {"message": DEL_REP_DATA, "ip": self.address.ip , "port": self.address.ports, "nodeID": self.nodeID, "startID" : p3, "endID": p2 }
        self.send_request(address1,data=data)

        address2 = (self.node_address[s2].ip,SERVER_PORT)
        notify_data(f"Sending DEL_REP_DATA to sucessor of my sucessor : node {s2}","GetData")
        data = {"message": DEL_REP_DATA, "ip": self.address.ip , "port": self.address.ports, "nodeID": self.nodeID, "startID" : p2, "endID": p1 }
        self.send_request(address2,data=data)

    def initialize_data(self,db_name):
        shutil.copyfile(db_name,self.db.db_name)
