import json
import socket
from backend.app.models.db_model import GType, Privacity, State, notify_data
from backend.chord.chord import Address, hash_key, send_request
from contants import *
import time 

class Client:
    
    def __init__(self, my_address):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind(my_address)
        self.receiver.listen()
        self.addr: Address = my_address

        # Descubrir un servidor al iniciar
        discovered_server = self.discover_server()
        if discovered_server:
            self.server_addr = Address(discovered_server[0], [discovered_server[1]])
            print(f"Connected to server {self.server_addr}")
        else:
            raise ConnectionError("No available Chord servers found!")


    def discover_server(self):
        """ Envía una solicitud multicast para obtener un servidor disponible. """
        multicast_group = (MCAST_GRP, MCAST_PORT)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Configurar el tiempo de espera para no bloquear indefinidamente
        sock.settimeout(2)

        try:
            # Enviar solicitud al grupo multicast
            message = "DISCOVER"
            sock.sendto(message.encode(), multicast_group)

            # Esperar respuesta
            data, server = sock.recvfrom(1024)
            server_ip, server_port = data.decode().split(":")
            print(f"Discovered server: {server_ip}:{server_port}")
            return server_ip, int(server_port)

        except socket.timeout:
            print("No response from multicast router")
            return None

        finally:
            sock.close()

   
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
    
    def create_account(self, user_key, user_name, last_name, password,address=None):
        if not address: 
            address = self.server_addr
        self.user_key = hash_key(user_key)
        name, last = self.check_account(self.user_key,address)
        if not name:
            data = {"message": CREATE_PROFILE, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": self.user_key, "user_name": user_name, "last_name": last_name, "password": password  }
            print(f"Sending CREATE_PROFILE request to {str(address)}")
            send_request(address,data=data)
            return True
        return False    

    def get_account(self, user_key, password,address=None):
        self.user_key = hash_key(user_key)
        return self.check_account(self.user_key,address,password=password)
    
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

    def create_personal_event(self, user_key, event_name, date_initial, date_end, privacity=Privacity.Public.value, state=State.Personal.value, id_group=None, id_creator=None,id_event=None, total=None, address=None):
        if not address: address = self.server_addr
        if id_event is None:
            _,_,_,_,_,_,_,_,sizes = self.get_all_events(user_key,address=address)
            total = max(sizes) + 1 if len(sizes) > 0 else 1
            user = user_key
            idcurrent = hash_key(f'{user}_{total}')
            id_event = str(idcurrent)
        data = {"message": CREATE_EVENT, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": user_key, "id_event" : id_event, "event_name": event_name, 
                "date_initial": date_initial , "date_end": date_end, "visibility": privacity, "state": state, "group":id_group, "creator":id_creator, "size": total  }
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

    def check_account(self,user_key,address,password = None):
        if not address: address = self.server_addr
        request = GET_PROFILE
        data = {"message": request, "ip": self.addr.ip, "port": self.addr.ports[0], "user_key": user_key, "password": password, "sender_addr": self.addr  }
        print(f"Sending GET_PROFILE request to {str(address)}")
        send_request(address,data=data)
        data = self.recieve_data(request)       
        return data['user_name'], data['last_name']

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
        request = GET_GROUP_TYPE
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
        request = GET_HIERARCHICAL_MEMBERS
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