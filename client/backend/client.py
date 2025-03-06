import hashlib
import json
import os
import socket
import zipfile

from sqlalchemy import Enum
from contants import *


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
    

def send_request(address,data=None,answer_requiered=False,expected_zip_file=False,num_bytes=1024):     
            sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try : 
                sender.connect(address)
            except ConnectionRefusedError as e :
                sender.close()
                return None
                #print("Error de conexion :", e)
                
            # establecer un tiempo de espera de 10 segundos
            sender.settimeout(10)
            if data:
                json_data = json.dumps(data).encode('utf-8')
                sender.send(json_data)
            else: 
                send_copy_db(sender,num_bytes)

            if answer_requiered:
              try:
                # Esperar la llegada de un mensaje
                
                if not expected_zip_file:
                  data = sender.recv(num_bytes)
                  data = data.decode('utf-8')
                  data = json.loads(data) 
                  sender.close()
                else:
                    data = recieve_copy_db(sender,num_bytes)
              except socket.timeout:
                # Manejar la excepción si se agotó el tiempo de espera
                if not expected_zip_file or not data: notify_data("Tiempo de espera agotado para recibir un mensaje","Error")
            sender.close()
            return data 

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
    
    def __init__(self, my_address):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind(my_address)
        self.receiver.listen()
        self.addr: Address = my_address
        self.servers = {}

        # Descubrir un servidor al iniciar
        discovered_server = self.discover_servers()
        if discovered_server:
            self.server_addr = Address(discovered_server[0], [discovered_server[1]])
            print(f"Connected to server {self.server_addr}")
        else:
            raise ConnectionError("No available Chord servers found!")


    def discover_servers(self):
        multicast_group = (MCAST_GRP,MCAST_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(multicast_group)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, 
                        socket.inet_aton(multicast_group[0]) + socket.inet_aton('0.0.0.0'))
            while True:
                data, _ = s.recvfrom(4096)
                message = data.decode()
                if message.startswith("AVAILABLE"):
                    _, node_id, ip, ports = message.split(':')
                    self.servers[node_id] = (ip, int(ports[0]))
                    print(f"Discovered server {node_id} at {ip}:{ports[0]}")

   
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
    


################################### USERS ##########################################
    def create_account(self, user_email, user_name, password, address=None):
        if not address:
            address = self.server_addr
        self.user_key = hash_key(user_email)
        if not self.check_account(self.user_key, address):
            data = {
                "message": CREATE_PROFILE,
                "ip": self.addr.ip,
                "port": self.addr.ports[0],
                "user_key": self.user_key,
                "user_name": user_name,
                "user_email": user_email,
                "password": password
            }
            print(f"Sending CREATE_PROFILE request to {str(address)}")
            response = send_request(address, data=data)
        return response
    
    def get_account(self, user_key, address=None, password=None):
        if not address:
            address = self.server_addr
        request = GET_PROFILE
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_key,
            "password": password,
            "sender_addr": self.addr
        }
        print(f"Sending GET_PROFILE request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response.get('user_name'), response.get('user_email')
        return None, None

    def check_account(self, user_key, address=None):
        if not address:
            address = self.server_addr
        name, email = self.get_account(user_key, address)
        return name is not None
    
    def get_user_by_email(self, user_email):
        user_key = hash_key(user_email)
        name, email = self.get_account(user_key)
        if name:
            return {"id": 1, "name": name, "email": email}
        return None
    
    def delete_user(self, user_id):
        request = DELETE_USER
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_USER request to {str(self.server_addr)}")
        response = send_request(self.server_addr, data=data)
        if response:
            return response
        return None
    
    def get_events(self, user_id):
        request = GET_EVENTS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_EVENTS request to {str(self.server_addr)}")
        response = send_request(self.server_addr, data=data)
        if response:
            return response.get("events", [])
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
            "id_event": event_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_EVENT request to {str(self.server_addr)}")
        response = send_request(self.server_addr, data=data)
        if response:
            return response
        return None
    
    def update_event(self, event_id, new_description, new_start_time, new_end_time, new_state, user_id):
        request = UPDATE_EVENT
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "id_event": event_id,
            "new_description": new_description,
            "new_start_time": new_start_time,
            "new_end_time": new_end_time,
            "new_state": new_state,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_EVENT request to {str(self.server_addr)}")
        response = send_request(self.server_addr, data=data)
        if response:
            return response
        return None
    
    def create_meeting(self, users_email, state, event_id, user_id, address=None):
        if not address:
            address = self.server_addr
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
        response = send_request(address, data=data)
        if response:
            return response
        return None
    
    def get_meetings(self, user_id, address=None):
        if not address:
            address = self.server_addr
        request = GET_MEETINGS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_MEETINGS request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response.get("meetings", [])
        return []

    def get_meeting_by_id(self, meeting_id, user_id):
        if not address:
            address = self.server_addr
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
        response = send_request(address, data=data)
        if response:
            return response
        return None

    def delete_meeting(self, meeting_id, user_id, address=None):
        if not address:
            address = self.server_addr
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
        response = send_request(address, data=data)
        if response:
            return response
        return None

    def update_meeting(self, meeting_id, new_event_id, new_state, user_id, address=None):
        if not address:
            address = self.server_addr
        request = UPDATE_MEETING
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "meeting_id": meeting_id,
            "new_event_id": new_event_id,
            "new_state": new_state,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_MEETING request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response
        return None
    
    def create_group(self, group_name, group_type,address=None):
        if not address: address = self.server_addr
        _,_,_,_,sizes = self.get_groups_belong_to(address)
        total = max(sizes) + 1 if len(sizes) > 0 else 1
        user = self.user_key
        idcurrent = hash_key(f'{user}_{total}')
        id_group = str(idcurrent)
        data = {"message": CREATE_GROUP, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_group": id_group, "group_name": group_name, "group_type": group_type, "size": total   }
        print(f"Sending CREATE_GROUP request to {str(address)}")
        send_request(address,data=data)


    def update_hierarchy_level(self, user_id, group_id, hierarchy, address=None):
        if not address:
            address = self.server_addr
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
        response = send_request(address, data=data)
        if response:
            return response
        return None
    
    def get_hierarchy_level(self, user_id, group_id, address=None):
        if not address:
            address = self.server_addr
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
        response = send_request(address, data=data)
        if response:
            return response.get("hierarchy_level")
        return None

    def add_user_to_group(self, user_id, group_id, hierarchy, address=None):
        if not address:
            address = self.server_addr
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
        print(f"Sending ADD_USER_TO_GROUP request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response
        return None

    def get_group_by_id(self, group_id, address=None):
        if not address:
            address = self.server_addr
        request = GET_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_GROUP_BY_ID request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response
        return None
    
    def update_group(self, group_id, group_update, address=None):
        if not address:
            address = self.server_addr
        request = UPDATE_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "group_id": group_id,
            "group_update": group_update,
            "sender_addr": self.addr
        }
        print(f"Sending UPDATE_GROUP request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response
        return None

    def delete_group(self, group_id, address=None):
        if not address:
            address = self.server_addr
        request = DELETE_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending DELETE_GROUP request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response
        return None

    def get_user_groups(self, user_id, address=None):
        if not address:
            address = self.server_addr
        request = GET_GROUPS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_USER_GROUPS request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response.get("groups", [])
        return []
    
    def remove_user_from_group(self, user_to_remove_id, group_id, address=None):
        if not address:
            address = self.server_addr
        request = DELETE_MEMBER_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_to_remove_id,
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending REMOVE_USER_FROM_GROUP request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response
        return None

    def get_users_in_group(self, group_id, address=None):
        if not address:
            address = self.server_addr
        request = GET_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "group_id": group_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_USERS_IN_GROUP request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response.get("users", [])
        return []
    
    def get_events_in_group(self, group_id, user_id, address=None):
        if not address:
            address = self.server_addr
        request = GET_GROUP
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "group_id": group_id,
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_EVENTS_IN_GROUP request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response.get("events", [])
        return []

    def create_group_meeting(self, users_email, state, event_id, user_id, group_id, address=None):
        if not address:
            address = self.server_addr
        data = {
            "message": CREATE_MEETING,
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
        response = send_request(address, data=data)
        if response:
            return response
        return None
    
    def get_invited_groups(self, user_id, address=None):
        if not address:
            address = self.server_addr
        request = GET_GROUPS
        data = {
            "message": request,
            "ip": self.addr.ip,
            "port": self.addr.ports[0],
            "user_key": user_id,
            "sender_addr": self.addr
        }
        print(f"Sending GET_INVITED_GROUPS request to {str(address)}")
        response = send_request(address, data=data)
        if response:
            return response.get("invited_groups", [])
        return []

    def get_notifications(self,address=None):
        if not address: address = self.server_addr
        request = GET_NOTIFICATIONS
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "sender_addr": self.addr  }
        print(f"Sending GET_NOTIFICATIONS request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data['ids'], data['texts']

    def delete_notification(self, id_notification,address=None):
        if not address: address = self.server_addr
        data = {"message": DELETE_NOTIFICATION, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_notification": id_notification  }
        print(f"Sending DELETE_NOTIFICATION request to {str(address)}")
        send_request(address,data=data)

    def create_event(self, user_key, event_name, date_initial, date_end, privacity=Privacity.Public.value, state=State.Personal.value , address=None):
        if not address: address = self.server_addr
        if id_event is None:
            _,_,_,_,_,_,_,_,sizes = self.get_all_events(user_key,address=address)
            total = max(sizes) + 1 if len(sizes) > 0 else 1
            user = user_key
            idcurrent = hash_key(f'{user}_{total}')
            id_event = str(idcurrent)
        data = {"message": CREATE_EVENT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": user_key, "id_event" : id_event, "event_name": event_name, 
                "date_initial": date_initial , "date_end": date_end, "visibility": privacity, "state": state }
        print(f"Sending CREATE_EVENT request to {str(address)}")
        send_request(address,data=data)
    
    def get_all_events(self,user_key=None,privacity=False,address=None):
        if not address: address = self.server_addr
        request = GET_EVENTS
        userkey = user_key if user_key else self.user_key
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": userkey, "privacity": privacity , "sender_addr": self.addr  }
        print(f"Sending GET_EVENTS request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids_event"],data["event_names"],data["dates_ini"],data["dates_end"],data["states"],data["visibilities"],data["creators"],data["id_groups"],data["sizes"]

    def get_groups_belong_to(self,address=None):
        if not address: address = self.server_addr
        request = GET_GROUPS
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "sender_addr": self.addr  }
        print(f"Sending GET_GROUPS request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids_group"],data["group_names"],data["group_types"],data["group_refs"],data["sizes"]
    
    def get_event(self, user_key, id_event, address=None):
        if not address: address = self.server_addr
        request = GET_EVENT
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": user_key, "id_event": id_event, "sender_addr": self.addr  }
        print(f"Sending GET_EVENT request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["id_event"],data["event_name"],data["date_ini"],data["date_end"],data["state"],data["visibility"],data["creator"],data["id_group"],data["size"]



    def delete_event(self, id_event,address=None):
        if not address: address = self.server_addr
        _,_,_,_,state,_,id_creator,id_group,_ = self.get_event(self.user_key,id_event,address)
        assert (id_creator and int(id_creator) == self.user_key) or state == State.Personal.value
        if id_group == None: self.delete_user_event(self.user_key,id_event,address)
        else:
            id_creator = int(id_creator)
            gtype = self.get_group_type(id_creator,id_group,address)
            if gtype == GType.Non_hierarchical.value: 
                ids_user,_ = self.get_inferior_members(id_creator,id_group,str(id_creator),address)
                members = ids_user
            else: members = self.get_equal_members(id_creator,id_group,address)
            for id_user in members: self.delete_user_event(int(id_user),id_event,address)

    def delete_user_event(self,user_key,id_event,address):
        data = {"message":DELETE_EVENT, "ip":self.addr.ip, "port":self.addr.ports[0], "user_key":user_key, "id_event":id_event  }
        print(f"Sending DELETE_EVENT request to {str(address)}")
        send_request(address,data=data)

    def get_group_type(self, id_creator, id_group, address=None):
        if not address: address = self.server_addr
        request = GET_GROUP
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_creator, "id_group": id_group, "sender_addr": self.addr  }
        print(f"Sending GET_GROUP_TYPE request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["group_type"]
    
    def accept_pendient_event(self, id_event,address=None):
        if not address: address = self.server_addr
        data = {"message": ACCEPT_EVENT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_event": id_event  }
        print(f"Sending ACCEPT_EVENT request to {str(address)}")
        send_request(address,data=data)

    def decline_pendient_event(self, id_event,address=None):
        if not address: address = self.server_addr
        _,_,_,_,state,_,id_creator,id_group,_ = self.get_event(self.user_key,id_event,address)
        assert state == State.Pendient.value
        members = self.get_equal_members(int(id_creator),id_group,address)
        print(f"Sending DECLINE_EVENT request to {str(address)}")
        for id_user in members: self.delete_user_event(int(id_user),id_event,address)

    def create_groupal_event(self, event_name, date_initial, date_end, id_group, address=None):
        if not address: address = self.server_addr
        _,_,_,_,_,_,_,_,sizes = self.get_all_events(self.user_key,address=address)
        total = max(sizes) + 1 if len(sizes) > 0 else 1
        idcurrent = hash_key(f'{self.user_key}_{total}')
        id_event = str(idcurrent)
        gtype = self.get_group_type(self.user_key,id_group,address)
        if gtype == GType.Hierarchical.value: 
            ids_user,_ = self.get_inferior_members(self.user_key,id_group,str(self.user_key),address)
            members = ids_user
        else: members = self.get_equal_members(self.user_key,id_group,address)
        for id_user in members: 
            if id_user == str(self.user_key): self.create_personal_event(self.user_key,event_name,date_initial,date_end,Privacity.Public.value,State.Asigned.value,id_group,str(self.user_key),id_event,total,address)
            elif gtype == GType.Hierarchical.value: self.create_personal_event(int(id_user),event_name,date_initial,date_end,Privacity.Public.value,State.Asigned.value,id_group,str(self.user_key),id_event,total,address)
            else: self.create_personal_event(int(id_user),event_name,date_initial,date_end,Privacity.Public.value,State.Pendient.value,id_group,str(self.user_key),id_event,total,address)

    def add_member(self, id_group, id_user, group_name, group_type, size, role=None, level=None,address=None):
        id_user = int(id_user)
        if not address: address = self.server_addr
        user_name, last_name = self.check_account(id_user,address)
        if  user_name:
            self.add_member_group(id_group,id_user,role,level,address)
            self.add_member_account(id_user,id_group, group_name, group_type, str(self.user_key),size,address)
            return True
        return False

    def add_member_group(self,id_group,id_user,role,level,address=None):
        if not address: address = self.server_addr
        data = {"message": ADD_MEMBER_GROUP, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "id_group": id_group, "id_user": id_user,"role": role, "level": level  }
        print(f"Sending ADD_MEMBER_GROUP request to {str(address)}")
        send_request(address,data=data)

    def add_member_account(self,id_user, id_group, group_name, group_type, ref, size,address=None):
        if not address: address = self.server_addr
        data = {"message": ADD_MEMBER_ACCOUNT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_user, "id_group": id_group, "group_name": group_name, "group_type": group_type, "id_ref": ref, "size": size  }
        print(f"Sending ADD_MEMBER_ACCOUNT request to {str(address)}")
        send_request(address,data=data)

    def get_inferior_members(self, id_creator, id_group,id_user,address=None):
        if not address: address = self.server_addr
        request = GET_HIERARCHY_LEVEL
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_creator, "id_group": id_group,"id_user": id_user, "sender_addr": self.addr  }
        print(f"Sending GET_HIERARCHICAL_MEMBERS request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids"],data["roles"]

    def get_equal_members(self, id_creator, id_group,address=None):
        if not address: address = self.server_addr
        request = GET_NON_HIERARCHICAL_MEMBERS
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": id_creator, "id_group": id_group, "sender_addr": self.addr  }
        print(f"Sending GET_NON_HIERARCHICAL_MEMBERS request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request) 
        return data["ids"]
        
    def get_member_events(self, id_member, address=None):
        id_member = int(id_member)
        if not address: address = self.server_addr
        return self.get_all_events(id_member,True,address)