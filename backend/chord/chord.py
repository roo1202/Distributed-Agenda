
import hashlib
import json
import os
import socket
import threading
import time
import zipfile
from backend.app.models.db_model import DBModel, notify_data

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
            try : sender.connect(address)
            except ConnectionRefusedError as e :
                sender.close()
                return None
                #print("Error de conexion :", e)
                
            # establecer un tiempo de espera de 10 segundos
            sender.settimeout(10)
            if data:
                json_data = json.dumps(data).encode('utf-8')
                sender.send(json_data)
            else: send_copy_db(sender,num_bytes)

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

def send_copy_db(conn,num_bytes = 1024):
        f = open ("copia.db", "rb")
        l = f.read(num_bytes)
        while (l):
            conn.send(l)
            l = f.read(num_bytes)
        os.remove("copia.db")

def recieve_copy_db(conn,num_bytes = 1024):
    data= False
    f = open("copia.db",'wb') #open in binary     
    # receive data and write it to file
    l = conn.recv(num_bytes)                  
    while (l):
          data = True
          f.write(l)
          l = conn.recv(num_bytes)
    f.close()
    return data


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


class ChordNode:

    def __init__(self,address:Address,local = False):

        self.address=address
        self.leader = None
        self.nodeSet = []                           # Nodes discovered so far
        self.local = local 
        self.database = {}

        #Setting node ID
        key = address.ip if not local else str(self.address)
        self.nodeID = hash_key(key) 
        self.db = DBModel(self.nodeID)
        self.nBits = 160
        self.Sucessor = None
        
       
        #Initializing Finger Table
        self.FT = [None for i in range(self.nBits+1)]

        self.MAXPROC = pow(2,160)
        self.node_address = {}

        #initializing sockets
        
        #Cuando otro nodo de la red quiera saber si este nodo esta, debe conectarse a este socket o 
        # si este nodo es el lider el resto se conecta a este socket para actualizar su lista de nodos
        
        self.discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.discover.bind((self.address.ip, int(self.address.ports[1])))
        self.discover.listen()

        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind((self.address.ip, int(self.address.ports[0])))
        self.receiver.listen()

        #Puerto para recibir archivos
        self.file_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_receiver.bind((self.address.ip, int(self.address.ports[2])))
        self.file_receiver.listen()

        #Puerto para chequeos
        self.check_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.check_receiver.bind((self.address.ip, int(self.address.ports[3])))
        self.check_receiver.listen()


        self.join()

        self.discover_resp_thread = threading.Thread(target=self.get_discover_request)
        self.discover_resp_thread .start()

        self.run()

    
    @property
    def Predecessor(self):
        return self.FT[0]
    
    @property 
    def Req_Method(self):
        return { CREATE_PROFILE: self.create_account , CREATE_GROUP: self.create_group, REP_GROUP:self.create_group, CREATE_EVENT: self.create_event, REP_PROFILE: self.create_account, GET_GROUP_TYPE:self.get_group_type,
                GET_PROFILE: self.get_account,GET_GROUPS: self.get_groups_belong_to, GET_EVENTS:self.get_all_events,REP_EVENT: self.create_event, GET_NOTIFICATIONS: self.get_notifications,GET_EVENT:self.get_event,
                DELETE_NOTIFICATION:self.delete_notification,DELETE_NOTIFICATION_REP:self.delete_notification, ACCEPT_EVENT: self.accept_pendient_event,ACCEPT_EVENT_REP:self.accept_pendient_event, DELETE_EVENT: self.delete_event,
                GET_NON_HIERARCHICAL_MEMBERS:self.get_equal_members, GET_HIERARCHICAL_MEMBERS:self.get_inferior_members, ADD_MEMBER_ACCOUNT:self.add_member_account, ADD_MEMBER_ACCOUNT_REP:self.add_member_account,
                ADD_MEMBER_GROUP:self.add_member_group, ADD_MEMBER_GROUP_REP:self.add_member_group}
    

    @property
    def Serialize_Address(self):
        return { node : (address.ip,address.ports) for node,address in self.node_address.items()}

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
    
    def recomputeFingerTable(self,write_to_new_suc = False):
        if len(self.nodeSet) > 1:
            self.FT[0]  = self.nodeSet[self.nodeSet.index(self.nodeID)-1] # Predecessor
            self.FT[1:] = [self.finger(i) for i in range(1,self.nBits+1)] # Sucessors
        elif len(self.nodeSet)  == 1: self.FT = [self.nodeSet[0] for i in range(1,self.nBits+1)]
        if not self.Sucessor: 
            self.Sucessor = self.FT[1] 
            return 
        if write_to_new_suc and not (self.Sucessor == self.nodeID) and not (self.Sucessor == self.FT[1]):
            self.Sucessor = self.FT[1]
            if  not (self.Sucessor == self.nodeID): self.send_data_to_sucessor()


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


    def recieve_checks(self):
        while True:
            conn, addr = self.check_receiver.accept()
            # conn es otro socket que representa la conexion 
            msg=conn.recv(1024)
            msg = msg.decode('utf-8')
            msg = json.loads(msg)         
            request = msg["message"]

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
                self.index_data(get_data,msg)
                send_copy_db(conn,num_bytes=5120)
                notify_data(f"Sending {response} to {node}","GetData")
                if not get_data: 
                    self.Sucessor= msg["nodeID"]
                    self.node_address[self.Sucessor] = Address(msg["ip"],msg["port"])
                elif msg["del_rep"]: self.delete_rep_data(msg)  

            if request == GET_NODES:
                id = msg["nodeID"]
                notify_data(f'Recieving GET_NODES request from {id}',"GetData")
                addresses = self.Serialize_Address
                data = {"message": SET_NODES,"ip": self.address.ip , "ports": self.address.ports , "nodeID": self.nodeID, "nodeSet":self.nodeSet, "addresses":addresses}
                data = json.dumps(data).encode('utf-8')
                conn.send(data)

            if request == SET_LEADER:
                id = msg["nodeID"]
                notify_data(f'Recieving SET_LEADER request from {id}',"Check")
                addresses,self.nodeSet = self.discover_nodes(True)
                self.node_address = self.get_addresses(addresses) 
                self.recomputeFingerTable(write_to_new_suc = True)       

            if request == DEL_REP_DATA:
                id = msg["nodeID"]
                notify_data(f"Receiving DEL_REP_DATA from {id}",'database')
                self.delete_rep_data(msg)

    def index_data(self,get_data,msg=None):
        start_index = self.Predecessor
        if msg:  start_index = msg["pred_pred"] if not get_data else msg["startID"]
        end_index =   self.nodeID  if not get_data else msg["nodeID"] 
        print(start_index,end_index)
        condition = lambda id : self.inbetween(int(id),start_index,end_index)
        self.db.get_filtered_db(condition,'copia.db')

    def delete_rep_data(self,msg):
        start_index = msg["pred_pred"]
        end_index =  msg["startID"]
        print(start_index,end_index)
        condition = lambda id : self.inbetween(int(id),start_index,end_index)
        self.db.delete_replicated_db(condition)

    def recieve_files(self):
        while True:          
            conn, addr = self.file_receiver.accept()
            notify_data(f"Receiving file from {addr}",'database')
            recieve_copy_db(conn,5120)
            self.db.replicate_db('copia.db')
            notify_data(f"Replicating data","database")
            self.db.check_db()
            os.remove('copia.db')

    def get_nodes(self):           
            data = {"message": GET_NODES, "ip": self.address.ip , "ports": self.address.ports, "nodeID": self.nodeID}
            leader_address = self.node_address[self.leader] 
            data = send_request((leader_address.ip,int(leader_address.ports[1])),data=data,answer_requiered=True)
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

    def check_sucessor(self):
        while True:
          time.sleep(20)
          if not self.Sucessor == self.nodeID:
            data = {"message": CHECK_SUC, "ip": self.address.ip , "ports": self.address.ports, "nodeID": self.nodeID, "leader":self.leader,"nodeSet":self.nodeSet}
            address = (self.node_address[self.Sucessor].ip,int(self.node_address[self.Sucessor].ports[3]))
            notify_data(f"Sending CHECK_SUC to {self.Sucessor}","Check")
            data = send_request(address,data=data,answer_requiered=True)
            notify_data(f'Recieving CHECK_SUC_RESP' ,"Check")
            if not data:
                if not self.leader == self.nodeID: self.get_nodes()  
        
    def send_data_to_sucessor(self):
        notify_data(f"New sucessor found {self.Sucessor}","Join")
        address = (self.node_address[self.Sucessor].ip,int(self.node_address[self.Sucessor].ports[2]))
        self.index_data(False)
        send_request(address,num_bytes=5120)
        notify_data(f"Sending REP_DATA to {self.Sucessor}","GetData")       
        

    def run(self):
        #Receiving requests
        while True:
            print("next_step")
            
            print(f"My address: {str(self.address)}")
            conn, addr = self.receiver.accept()
            msg=conn.recv(1024)
            msg = msg.decode('utf-8')
            data = json.loads(msg) 

            #unpacking data
            request = data["message"]
           
            if request == STOP: 
                break
            elif request in self.Req_Method.keys():
                notify_data(f"Receiving {request} from {addr}","SetData")
                if 30 <= int(request) < 60:
                    if not self.leader == self.nodeID: self.get_nodes()   
                    if int(request)%2 ==0 :self.update_key(data,request,addr)
                    else: 
                        self.Req_Method[request](data)
                        self.db.check_db()
                if 60 <= int(request) < 80:
                   if not self.leader == self.nodeID: self.get_nodes()
                   self.get_key(data,request)

       
            
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
                    send_request((self.node_address[nextID].ip,int(self.node_address[nextID].ports[0])),data=data)
                    notify_data(f"Sending LOOKUP_REQ to {nextID} node ","Get_Data")
                else:
                    data = {"message": LOOKUP_REP, "ip": self.address.ip , "port": self.address.ports[0], "node":  nextID,"key":key}        
                    send_request((ip,int(port)),data=data)               

    def update_key(self,data,request,addr):
                key = data["user_key"]
                nextID = self.localSuccNode(key)          # look up next node #-
                
                if not nextID == self.nodeID :
                    #data = {"message": request, "ip": ip , "port": self.address.ports[0], "user_key": key } # send to succ                    
                    notify_data(f"Sending {request}  to {nextID}: {str(self.node_address[nextID])} node ","SetData")
                    send_request((self.node_address[nextID].ip,int(self.node_address[nextID].ports[0])),data=data)
                else :
                    self.Req_Method[request](data)
                    self.db.check_db()
                    next_node = self.FT[1]
                    if not self.nodeID == next_node:
                        notify_data(f"Sending {int(request)+1} to {next_node}","SetData")
                        #data = {"message": str(int(request)+1), "ip": self.address.ip , "port": self.address.ports[0], "node":  nextID,"user_key":key}
                        data["message"] = str(int(request)+1)
                        send_request((self.node_address[next_node].ip,int(self.node_address[next_node].ports[0])),data=data)




    def get_key(self,data,request):            
                key = data["user_key"]
                sender_addr = data["sender_addr"]
                nextID = self.localSuccNode(key)          # look up next node #-
                if not nextID == self.nodeID :
                    #data = {"message": request, "ip": ip , "port": port, "key": key,"sender_addr":sender_addr } # send to succ 
                    send_request((self.node_address[nextID].ip,int(self.node_address[nextID].ports[0])),data=data)
                    notify_data(f"Sending {request} to {nextID} node : {str(self.node_address[nextID])} ","GetData")
                else:
                    data = self.Req_Method[request](data)
                    #data = self.get_data(data,int(request)+1)
                    notify_data(f"Sending  {int(request)+1} to {sender_addr}","GetData")
                    send_request((sender_addr[0],sender_addr[1]),data=data)
                    
    def set_data(self,data):
        key = data["key"]
        value = data["value"]
        self.database[key] = value
        notify_data(f"Set {value} to {key} key","SetData")

    def get_data(self,data):
        key = data["key"]
        try: value = self.database[key] 
        except KeyError:
           notify_data(colored(f"Key {key} not found","Error"))
           return None
        notify_data(f"Obtained {value} to {key} key","GetData")
        return value              
    
    def create_account(self,data):
        self.db.create_account(data["user_key"],data["user_name"],data["last_name"],data["password"])

    def get_account(self,data):
        response = str(int(data["message"])+1)
        user_name,last_name=self.db.get_account(data["user_key"],data["password"])
        resp_data = {"message": str(response),'user_name':user_name,'last_name':last_name}
        if not user_name: notify_data("This account doesn't exist","Error")
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data
    
    def create_group(self,data):
        self.db.create_group(data["user_key"],data["id_group"],data["group_name"],data["group_type"],data["size"])
    
    def get_notifications(self,data):
        ids,texts=self.db.get_notifications(data["user_key"])
        resp_data = {"message": GET_NOTIF_RESP,'ids': ids,'texts': texts}
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data

    def delete_notification(self,data):
        self.db.delete_notification(data["user_key"],data["id_notification"])

    def create_event(self,data):
        self.db.create_event(data["user_key"],data["id_event"],data["event_name"],data["date_initial"],data["date_end"],data["state"],data["visibility"],data["group"],data["creator"],data["size"])




    def get_all_events(self,data):
        idevents,enames,datesc,datesf,states,visibs,creators,idgroups,sizes=self.db.get_all_events(data["user_key"],data["privacity"])
        resp_data = {"message": GET_EVENTS_RESP, "ids_event": idevents, "event_names": enames, "dates_ini": datesc, "dates_end": datesf, 
                     "states": states, "visibilities": visibs, "creators": creators, "id_groups": idgroups, "sizes":sizes  }
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data
    
    def delete_event(self,data):
        user_key = data["user_key"] 
        id_event = data["id_event"]
        self.db.delete_event(user_key,id_event) 
    
    def get_groups_belong_to(self,data):
        idsgroup,gnames,gtypes,refs,sizes = self.db.get_groups_belong_to(data["user_key"])
        resp_data = {"message": GET_GROUPS_RESP, "ids_group": idsgroup, "group_names": gnames, "group_types": gtypes, "group_refs": refs, "sizes":sizes  }
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data 
      
    def accept_pendient_event(self,data):
        self.db.accept_pendient_event(data["user_key"],data["id_event"])

    def get_event(self,data):
        event,ename,datec,datef,state,visib,creator,group,size = self.db.get_event(data["user_key"],data["id_event"])
        resp_data = {"message": GET_EVENT_RESP, "id_event": event, "event_name": ename, "date_ini": datec, "date_end": datef, 
                     "state": state, "visibility": visib, "creator": creator, "id_group": group, "size":size  }
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data
    
    def get_group_type(self,data):
        gtype = self.db.get_group_type(data["user_key"],data["id_group"])
        resp_data = {"message": GET_GROUP_TYPE_RESP, "group_type": gtype  }
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data
    
    def get_equal_members(self,data):
        ids = self.db.get_equal_members(data["id_group"])
        resp_data = {"message": GET_NON_HIER_MEMB_RESP, "ids": ids  }
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data
    
    def get_inferior_members(self,data):
        ids,roles = self.db.get_inferior_members(data["id_user"],data["id_group"])
        resp_data = {"message": GET_HIER_MEMB_RESP, "ids": ids, "roles": roles  }
        resp_data["ip"] = data["ip"] 
        resp_data["port"] = data["port"] 
        resp_data["sender_addr"] = data["sender_addr"]
        return resp_data
    
    def add_member_group(self,data):
        self.db.add_member_group(data["id_group"],data["id_user"],data["role"],data["level"])

    def add_member_account(self,data):
        self.db.add_member_account(data["user_key"],data["id_group"],data["group_name"],data["group_type"],data["id_ref"],data["size"])
