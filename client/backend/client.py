import hashlib
import json
import os
import socket
import threading
import time
import zipfile

from sqlalchemy import Enum
from contants import *



def hash_key(key: str) -> int:
    """
    Función de hash que calcula el hash SHA-1 de una cadena de caracteres y devuelve un número entero que se utiliza como la clave del nodo en la red Chord.
    """
    sha1 = hashlib.sha1(key.encode('utf-8'))
    hash_value = int(sha1.hexdigest(), 16) 
    string_num = str(hash_value)
    new_string = string_num[:16]
    return int(new_string)


class Address():
    def __init__(self,ip,ports):
        self.ip = ip
        self.ports = ports

    def __str__(self):
        return f"tcp:{self.ip}:{self.ports[0]}"
    
    def __repr__(self):
        return f"ip:{self.ip} ports:{self.ports}"
    

def notify_data(data,data_type):
	print(data_type + ": " + data)


class Privacity(Enum):
    Public = "Público"
    Private = "Privado"

class GType(Enum):
    Hierarchical = "Jerárquico"
    Non_hierarchical = "No Jerárquico"

class State(Enum):
    Asigned = "Asignado"
    Pendient = "Pendiente"
    Personal = "Personal"

    
class Client:
    def __init__(self):
        my_address = Address(socket.gethostbyname(socket.gethostname()), [5000])
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind((HOST, my_address.ports[0]))
        self.receiver.listen()
        self.addr: Address = my_address
        self.servers = {}

        print('Iniciando cliente con address: %s' % my_address)

        # Hilo para conocer los servidores activos 
        # self.servers_listener = threading.Thread(target=self.listen_servers)
        # self.servers_listener.daemon=True
        # self.servers_listener.start()

        # # Hilo para limpiar servidores caídos
        # self.cleanup_servers_thread = threading.Thread(target=self.cleanup_servers)
        # self.cleanup_servers_thread.daemon =True
        # self.cleanup_servers_thread.start()

        time.sleep(5)

        # self.send_request(address=self.server_addr(), data='Hola desde el cliente')


    def send_request(self, address, data=None, answer_required=True, num_bytes=1024):
        sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not address:
            notify_data("No se encuentran servidores disponibles", "Info")
            return False
        try:
            sender.connect(address)
        except ConnectionRefusedError as e:
            print("Error de conexión:", e)
            sender.close()
            return None

        if data:
            # Obtener la dirección local del socket (ip y puerto efímero)
            data["sender_addr"] = sender.getsockname()
            json_data = json.dumps(data).encode('utf-8')
            sender.send(json_data)

        respuesta = None  # Variable para almacenar la respuesta

        if answer_required:
            sender.settimeout(10)  # Establecer timeout para la recepción
            try:
                # Recibir datos directamente del mismo socket
                respuesta = sender.recv(num_bytes)
                if respuesta:
                    respuesta = respuesta.decode('utf-8')
                    respuesta = json.loads(respuesta)
                    print('Respuesta obtenida:')
                    print(respuesta)
                else:
                    print("El servidor cerró la conexión sin enviar respuesta.")
            except socket.timeout:
                print('Tiempo de espera agotado.')
                if not respuesta:
                    notify_data("Tiempo de espera agotado para recibir respuesta", "Error")
            except Exception as e:
                print("Error al recibir respuesta:", e)
        sender.close()
        return respuesta


    def listen_servers(self):
            """Escucha mensajes multicast de los servidores."""
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
                        self.servers[node_id] = (Address(ip, [CLIENT_PORT]),time.time())
                        #print('Servidor descubierto en direccion : %s' % self.servers[node_id][0])
                        

    def cleanup_servers(self):
        """Elimina servidores inactivos de la lista."""
        while True:
            current_time = time.time()
            to_remove = [
                node_id
                for node_id, info in self.servers.items()
                if current_time - info[1] > SERVER_TIMEOUT
            ]
            for node_id in to_remove:
                del self.servers[node_id]
            time.sleep(10)
   
    def recieve_data(self,request):
        conn, addr = self.receiver.accept()
        msg=conn.recv(1024)
        msg = msg.decode('utf-8')
        data =  json.loads(msg)
        response = data["message"]
        if not response  == str(int(request)+1):
            notify_data(f"Worg data response type expected {str(int(request)+1)} and got {response}","Error")
        else:
            return data
        
    def server_addr(self):
        # if len(self.servers) > 0 :
        #     address = list(self.servers.values())[0][0]    # Listar el diccionario de servidores y devolver la direccion del primero
        #     return (address.ip, address.ports[0])
        # else:
        #     return False
        return ('127.0.0.1', 65434)
    

################################### USERS ##########################################
    def create_account(self, user_email, user_name, password):
        address = self.server_addr()
        user_key = hash_key(user_email)
        data = {
            "message": CREATE_PROFILE,
            "user_key": user_key,
            "user_name": user_name,
            "user_email": user_email,
            "password": password
        }
        print(f"Sending CREATE_PROFILE request to {str(address)}")
        response = self.send_request(address=address, data=data)
        return response
    
    def get_account(self, user_key, password=None):
        address = self.server_addr()
        request = GET_PROFILE
        data = {
            "message": request,
            "user_key": user_key,
            "password": password
        }
        print(f"Sending GET_PROFILE request to {str(address)}")
        response = self.send_request(address=address, data=data)
        if response:
            return response
        return None


    def check_account(self, user_key, address=None):
        if not address:
            address = self.server_addr()
        resp = self.get_account(user_key, address)
        return 'False' in resp
    
    def get_user_by_email(self, user_email):
        user_key = hash_key(user_email)
        resp = self.get_account(user_key)
        return resp
      
    
    def delete_user(self, user_id):
        request = DELETE_USER
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_USER request to {str(self.server_addr())}")
        response = self.send_request(self.server_addr(), data=data)
        if response:
            return response
        return None
    
    # Obtiene los eventos del usuario
    def get_events(self, user_id):
        request = GET_EVENTS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_EVENTS request to {str(self.server_addr())}")
        response = self.send_request(self.server_addr(), data=data)
        if response:
            return response
        return []
    
    def get_events_of(self, user_email):
        user_key = hash_key(user_email)
        return self.get_events(user_key)
    
    def delete_event(self, event_id, user_id):
        request = DELETE_EVENT
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "event_id": event_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_EVENT request to {str(self.server_addr())}")
        response = self.send_request(self.server_addr(), data=data)
        if response:
            return response
        return None
    
    def update_event(self, event_id, new_description, new_start_time, new_end_time, new_state, user_id, visibility):
        request = UPDATE_EVENT
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "event_id": event_id,
            "new_description": new_description,
            "new_start_time": new_start_time,
            "new_end_time": new_end_time,
            "new_state": new_state,
            "visibility": visibility,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_EVENT request to {str(self.server_addr())}")
        response = self.send_request(self.server_addr(), data=data)
        if response:
            return response
        return None
    
    def create_meeting(self, users_email, state, event_id, user_id):
        address = self.server_addr()
        data = {
            "message": CREATE_MEETING,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "users_email": users_email,
            "state": state,
            "event_id": event_id,
            "sender_addr": self.addr
        }
        print(f"Sending CREATE_MEETING request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None
    
    # Obtiene todas las reuniones de un usuario
    def get_meetings(self, user_id):
        address = self.server_addr()
        request = GET_MEETINGS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_MEETINGS request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return []

    def get_meeting_by_id(self, meeting_id, user_id):
        address = self.server_addr()
        request = GET_MEETING
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "meeting_id": meeting_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_MEETING_BY_ID request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None

    def delete_meeting(self, meeting_id, user_id):
        address = self.server_addr()
        request = DELETE_MEETING
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "meeting_id": meeting_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_MEETING request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None

    def update_meeting(self, meeting_id, new_state, user_id):
        address = self.server_addr()
        request = UPDATE_MEETING
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "meeting_id": meeting_id,
            "new_state": new_state,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_MEETING request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None
    
    def create_group(self, group_name, group_type, creator):
        address = self.server_addr()
        data = {
            "message": CREATE_GROUP, 
            "ip": self.addr.ip, 
            "port": self.addr.ports[0], 
            "user_key": creator, 
            "group_name": group_name, 
            "hierarchy": group_type 
            }
        print(f"Sending CREATE_GROUP request to {str(address)}")
        data = self.send_request(address,data=data)
        if data:
            return data
        return None


    def update_hierarchy_level(self, user_id, group_id, hierarchy):
        address = self.server_addr()
        request = UPDATE_HIERARCHY_LEVEL
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "group_id": group_id,
            "hierarchy": hierarchy,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_HIERARCHY_LEVEL request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None
    
    # esto debe retornar directamente el numero que representa la jerarquia
    def get_hierarchy_level(self, user_id, group_id):
        address = self.server_addr()
        request = GET_HIERARCHY_LEVEL
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_HIERARCHY_LEVEL request to {str(address)}")
        response = self.send_request(address, data=data)
        if response is not None:
            return response
        return None

    #esto debe retornar un grupo
    def add_user_to_group(self, user_id, group_id, hierarchy):
        address = self.server_addr()
        request = ADD_MEMBER_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "group_id": group_id,
            "hierarchy": hierarchy,
            "sender_addr": self.addr
        }
        print(f"Sending ADD_MEMBER_GROUP request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None

    def get_group_by_id(self, user_id, group_id):
        address = self.server_addr()
        request = GET_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key" : user_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_GROUP_BY_ID request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None
    
    def update_group(self, user_id, group_id, new_group_name, new_group_hierarchy):
        address = self.server_addr()
        request = UPDATE_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "group_id": group_id,
            "group_name": new_group_name,
            "group_hierarchy": new_group_hierarchy,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_GROUP request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None

    def delete_group(self, user_id, group_id):
        address = self.server_addr()
        request = DELETE_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_GROUP request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None

    # Obtiene los grupos de un usuario
    def get_user_groups(self, user_id):
        address = self.server_addr()
        request = GET_GROUPS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_GROUPS request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return []
    
    # esto debe retornar un grupo
    def remove_user_from_group(self, user_to_remove_id, group_id):
        address = self.server_addr()
        request = DELETE_MEMBER_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_to_remove_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_MEMBER_GROUP request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None

    # debe retornar una lista de emails
    def get_users_in_group(self, user_id, group_id):
        address = self.server_addr()
        request = GET_USERS_IN_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_USERS_IN_GROUP request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return []
    
    def get_events_in_group(self, group_id, user_id):
        address = self.server_addr()
        request = GET_EVENTS_IN_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "group_id": group_id,
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_EVENTS_IN_GROUP request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return []

    # debe retornar una reunion
    def create_group_meeting(self, users_email, state, event_id, user_id, group_id):
        address = self.server_addr()
        data = {
            "message": CREATE_GROUP_MEETING,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "users_email": users_email,
            "state": state,
            "event_id": event_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending CREATE_GROUP_MEETING request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return None
    
    # debe devolver una lista de grupos
    def get_invited_groups(self, user_id):
        address = self.server_addr()
        request = GET_INVITED_GROUPS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_INVITED_GROUPS request to {str(address)}")
        response = self.send_request(address, data=data)
        if response:
            return response
        return []

    def get_notifications(self, user_id):   # falta el endpoint
        if not address: address = self.server_addr()
        request = GET_NOTIFICATIONS
        data = {
            "message": request, 
            "ip": self.addr.ip, 
            "port": self.addr.ports[0], 
            "user_key": user_id, 
            "sender_addr": self.addr  }
        print(f"Sending GET_NOTIFICATIONS request to {str(address)}")
        data = self.send_request(address,data=data)
        if data:
            return data
        return []

    def delete_notification(self, id_notification,address=None):
        if not address: address = self.server_addr()
        data = {"message": DELETE_NOTIFICATION, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_notification": id_notification  }
        print(f"Sending DELETE_NOTIFICATION request to {str(address)}")
        self.send_request(address,data=data)

    def create_event(self, user_key, event_name, date_initial, date_end, privacity=Privacity.Public, state=State.Personal):
        address = self.server_addr()
        data = {"message": CREATE_EVENT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": user_key, "description": event_name, 
                "start_time": date_initial , "end_time": date_end, "visibility": privacity, "state": state }
        print(f"Sending CREATE_EVENT request to {str(address)}")
        resp = self.send_request(address,data=data)
        return resp
    
    def get_all_events(self,user_key=None,privacity=False,address=None):
        if not address: address = self.server_addr()
        request = GET_EVENTS
        userkey = user_key if user_key else self.user_key
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": userkey, "privacity": privacity , "sender_addr": self.addr  }
        print(f"Sending GET_EVENTS request to {str(address)}")
        self.send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids_event"],data["event_names"],data["dates_ini"],data["dates_end"],data["states"],data["visibilities"],data["creators"],data["id_groups"],data["sizes"]

    def get_groups_belong_to(self,address=None):
        if address is None: address = self.server_addr()
        request = GET_GROUPS
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "sender_addr": self.addr  }
        print(f"Sending GET_GROUPS request to {str(address)}")
        self.send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids_group"],data["group_names"],data["group_types"],data["group_refs"],data["sizes"]
    
    def get_event(self, user_key, id_event):
        address = self.server_addr()
        request = GET_EVENT
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": user_key, "event_id": id_event, "sender_addr": self.addr }
        print(f"Sending GET_EVENT request to {str(address)}")
        response = self.send_request(address,data=data)
        if response:
            return response 
        return None

    def delete_user_event(self,user_key,id_event,address):
        data = {"message":DELETE_EVENT, "ip":self.addr.ip, "port":self.addr.ports[0], "user_key":user_key, "id_event":id_event  }
        print(f"Sending DELETE_EVENT request to {str(address)}")
        self.send_request(address,data=data)

    def get_group_type(self, id_creator, id_group, address=None):
        if not address: address = self.server_addr()
        request = GET_GROUP
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_creator, "id_group": id_group, "sender_addr": self.addr  }
        print(f"Sending GET_GROUP_TYPE request to {str(address)}")
        self.send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["group_type"]
    
    def accept_pendient_event(self, id_event,address=None):
        if not address: address = self.server_addr()
        data = {"message": ACCEPT_EVENT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_event": id_event  }
        print(f"Sending ACCEPT_EVENT request to {str(address)}")
        self.send_request(address,data=data)

    def decline_pendient_event(self, id_event,address=None):
        if not address: address = self.server_addr()
        _,_,_,_,state,_,id_creator,id_group,_ = self.get_event(self.user_key,id_event,address)
        assert state == State.Pendient
        members = self.get_equal_members(int(id_creator),id_group,address)
        print(f"Sending DECLINE_EVENT request to {str(address)}")
        for id_user in members: self.delete_user_event(int(id_user),id_event,address)

    def create_groupal_event(self, event_name, date_initial, date_end, id_group, address=None):
        if not address: address = self.server_addr()
        _,_,_,_,_,_,_,_,sizes = self.get_all_events(self.user_key,address=address)
        total = max(sizes) + 1 if len(sizes) > 0 else 1
        idcurrent = hash_key(f'{self.user_key}_{total}')
        id_event = str(idcurrent)
        gtype = self.get_group_type(self.user_key,id_group,address)
        if gtype == GType.Hierarchical: 
            ids_user,_ = self.get_inferior_members(self.user_key,id_group,str(self.user_key),address)
            members = ids_user
        else: members = self.get_equal_members(self.user_key,id_group,address)
        for id_user in members: 
            if id_user == str(self.user_key): self.create_personal_event(self.user_key,event_name,date_initial,date_end,Privacity.Public,State.Asigned,id_group,str(self.user_key),id_event,total,address)
            elif gtype == GType.Hierarchical: self.create_personal_event(int(id_user),event_name,date_initial,date_end,Privacity.Public,State.Asigned,id_group,str(self.user_key),id_event,total,address)
            else: self.create_personal_event(int(id_user),event_name,date_initial,date_end,Privacity.Public,State.Pendient,id_group,str(self.user_key),id_event,total,address)

    def add_member(self, id_group, id_user, group_name, group_type, size, role=None, level=None,address=None):
        id_user = int(id_user)
        if not address: address = self.server_addr()
        user_name, last_name = self.check_account(id_user,address)
        if  user_name:
            self.add_member_group(id_group,id_user,role,level,address)
            self.add_member_account(id_user,id_group, group_name, group_type, str(self.user_key),size,address)
            return True
        return False

    def add_member_group(self,id_group,id_user,role,level,address=None):
        if not address: address = self.server_addr()
        data = {"message": ADD_MEMBER_GROUP, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_group": id_group, "id_user": id_user,"role": role, "level": level  }
        print(f"Sending ADD_MEMBER_GROUP request to {str(address)}")
        self.send_request(address,data=data)

    def add_member_account(self,id_user, id_group, group_name, group_type, ref, size,address=None):
        if not address: address = self.server_addr()
        data = {"message": ADD_MEMBER_ACCOUNT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_user, "id_group": id_group, "group_name": group_name, "group_type": group_type, "id_ref": ref, "size": size  }
        print(f"Sending ADD_MEMBER_ACCOUNT request to {str(address)}")
        self.send_request(address,data=data)

    def get_inferior_members(self, id_creator, id_group,id_user,address=None):
        if not address: address = self.server_addr()
        request = GET_HIERARCHY_LEVEL
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_creator, "id_group": id_group,"id_user": id_user, "sender_addr": self.addr  }
        print(f"Sending GET_HIERARCHICAL_MEMBERS request to {str(address)}")
        self.send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids"],data["roles"]

    def get_equal_members(self, id_creator, id_group,address=None):
        if not address: address = self.server_addr()
        request = GET_NON_HIERARCHICAL_MEMBERS
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_creator, "id_group": id_group, "sender_addr": self.addr  }
        print(f"Sending GET_NON_HIERARCHICAL_MEMBERS request to {str(address)}")
        self.send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids"]
        
    def get_member_events(self, id_member, address=None):
        id_member = int(id_member)
        if not address: address = self.server_addr()
        return self.get_all_events(id_member,True,address)