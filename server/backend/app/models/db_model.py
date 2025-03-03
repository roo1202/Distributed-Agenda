from .group import Group
from .meeting import Meeting
from sqlalchemy.orm import Session
from services.user_service import *
from services.meeting_service import *
from services.group_service import *
from services.event_service import *

from sqlalchemy import Enum, create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base

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

class DBModel:
    def __init__(self, id: int):
        # Creamos la URL de conexión de SQLAlchemy
        self.db_name = f"{id}.db"
        self.db_url = f"sqlite:///{self.db_name}"

        self.engine = create_engine(self.db_url, echo=False) 
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        Base.metadata.create_all(self.engine)


    def get_session(self) -> Session:
        """Devuelve una sesión nueva para interactuar con la base de datos."""
        return self.SessionLocal()

    def filter_function(self, condition, cls):
        """
        Devuelve una función que, dado un objeto 'row', verifique
        si 'row.user' o 'row.creator' cumple la condición.
        """
        def cond(row):
            key = row.user if cls != Group else row.creator 
            return condition(int(key))
        return cond 
    
    def get_filtered_db(self, condition, new_db_name):
        """
        1) Lee todos los registros de la base de datos actual.
        2) Crea otra base de datos (SQLite) con nombre `new_db_name`.
        3) Copia únicamente aquellos registros cuyo 'user' o 'creator' cumplan con 'condition'.
        """
        old_session = self.SessionLocal()
        registers = {}
        for cls in self.classes:
            registers[cls] = old_session.query(cls).all()
        old_session.close()

        engine_copia = create_engine(f"sqlite:///{new_db_name}", echo=False)
        SessionCopia = sessionmaker(bind=engine_copia, autoflush=False, autocommit=False)
        session_copia = SessionCopia()

        Base.metadata.create_all(engine_copia)

        for cls in self.classes:
            for origen_row in registers[cls]:
                if (cls != Group and condition(origen_row.user)) or (cls == Group and condition(origen_row.creator)):
                    data = {
                        col.name: getattr(origen_row, col.name) 
                        for col in cls.__table__.columns
                    }
                    dest_row = cls(**data)
                    session_copia.add(dest_row)

        session_copia.commit()
        session_copia.close()
        engine_copia.dispose()

    def replicate_db(self, db_name):
        """
        Copia todos los registros de 'db_name' (otra base de datos) a la base de datos actual.
        """
        engine_origen = create_engine(f"sqlite:///{db_name}", echo=False)
        SessionOrigen = sessionmaker(bind=engine_origen, autoflush=False, autocommit=False)
        session_origen = SessionOrigen()

        registers = {}
        for cls in self.classes:
            registers[cls] = session_origen.query(cls).all()
        session_origen.close()
        engine_origen.dispose()

        session_actual = self.SessionLocal()
        for cls in self.classes:
            for row in registers[cls]:
                data = {
                    col.name: getattr(row, col.name)
                    for col in cls.__table__.columns
                }
                new_row = cls(**data)
                session_actual.add(new_row)
        
        session_actual.commit()
        session_actual.close()


    def check_db(self):
        """
        Lee los datos de cada tabla y los imprime. Luego invoca notify_data()
        para informar qué datos se han consultado.
        """
        session = self.SessionLocal()
        registers = []
        for cls in self.classes:
            rows = session.query(cls).all()
            registers.append(rows)

        notify_data("Users", "GetData")
        for row in registers[0]:
            print(row.user, row.name, row.last, row.passw)

        notify_data("Notifications", "GetData")
        for row in registers[1]:
            print(row.user, row.notif, row.text)

        notify_data("Groups", "GetData")
        for row in registers[2]:
            print(row.creator, row.group, row.gname, row.gtype)

        notify_data("User-Group", "GetData")
        for row in registers[3]:
            print(row.user, row.group, row.ref)

        notify_data("Meetings", "GetData")
        for row in registers[4]:
            print(row.group, row.user, row.role, row.level)

        notify_data("Events", "GetData")
        for row in registers[5]:
            print(row.user, row.event, row.ename, row.datec, row.datef, row.state, row.visib, row.creator, row.group)

        session.close()


    def delete_replicated_db(self, condition):
        """
        Elimina de la base actual todos los registros que cumplan la condición:
            - Si cls != Group: condition(row.user)
            - Si cls == Group: condition(row.creator)
        """
        session = self.SessionLocal()
        for cls in self.classes:
            rows = session.query(cls).all()
            for origen_row in rows:
                if (cls != Group and condition(origen_row.user)) or (cls == Group and condition(origen_row.creator)):
                    session.delete(origen_row)

        session.commit()
        session.close()

        notify_data("Replicated data deleted.", 'database')      
        
        session.close()


    # Metodos para el manejo de la base de datos 

    def create_user(self, data):
        """
        Crea un nuevo usuario.
        """
        db = self.get_session()
        try:
            return create_user(db, data["user_name"], data["user_email"], data["password"])
        finally:
            db.close()
                
    def get_user_by_email(self, data):
        """
        Obtiene un usuario por su email.
        """
        db = self.get_session()
        try:
            return get_user_by_email(db, data["user_email"])
        finally:
            db.close()

    def get_user_by_id(self, data):
        """
        Obtiene un usuario por su ID.
        """
        db = self.get_session()
        try:
            return get_user_by_id(db, data["user_key"])
        finally:
            db.close()

    def get_users(self):
        """
        Obtiene todos los usuarios.
        """
        db = self.get_session()
        try:
            return get_users(db)
        finally:
            db.close()

    def update_user(self, data):
        """
        Actualiza el nombre de un usuario por su ID.
        """
        db = self.get_session()
        try:
            return update_user(db, data["user_key"], data["new_user_name"])
        finally:
            db.close()

    def delete_user(self, data):
        """
        Elimina un usuario por su ID.
        """
        db = self.get_session()
        try:
            return delete_user(db, data["user_key"])
        finally:
            db.close()

    def create_meeting(self, data):
        """
        Crea una nueva reunión.
        """
        db = self.get_session()
        try:
            return create_meeting(db, data["users_email"], data["state"], data["event_id"], data["user_key"])
        finally:
            db.close()

    def create_group_meeting(self, data):
        """
        Crea una nueva reunión de grupo.
        """
        db = self.get_session()
        try:
            return create_group_meeting(db, data["users_email"], data["state"], data["event_id"], data["user_key"], data["group_id"])
        finally:
            db.close()

    def add_meetings(self, data):
        """
        Agrega múltiples reuniones a la base de datos.
        """
        db = self.get_session()
        try:
            return add_meetings(db, data["meetings"])
        finally:
            db.close()

    def get_meeting_by_id(self, data):
        """
        Obtiene una reunión por su ID.
        """
        db = self.get_session()
        try:
            return get_meeting_by_id(db, data["meeting_id"], data["user_key"])
        finally:
            db.close()

    def get_meetings(self, data):
        """
        Obtiene todas las reuniones de un usuario.
        """
        db = self.get_session()
        try:
            return get_meetings(db, data["user_key"])
        finally:
            db.close()

    def update_meeting(self, data):
        """
        Actualiza una reunión por su ID.
        """
        db = self.get_session()
        try:
            return update_meeting(db, data["meeting_id"], data["new_event_id"], data["new_state"], data["user_key"])
        finally:
            db.close()

    def delete_meeting(self, data):
        """
        Elimina una reunión por su ID.
        """
        db = self.get_session()
        try:
            return delete_meeting(db, data["meeting_id"], data["user_key"])
        finally:
            db.close()

    def add_user_to_group(self, data):
        """
        Añade un usuario a un grupo.
        """
        db = self.get_session()
        try:
            return add_user_to_group(db, data["user_id"], data["group_id"], data.get("hierarchy_level", 0))
        finally:
            db.close()

    def remove_user_from_group(self, data):
        """
        Elimina un usuario de un grupo.
        """
        db = self.get_session()
        try:
            return remove_user_from_group(db, data["user_key"], data["group_id"])
        finally:
            db.close()

    def get_users_in_group(self, data):
        """
        Obtiene todos los usuarios que pertenecen a un grupo.
        """
        db = self.get_session()
        try:
            return get_users_in_group(db, data["group_id"])
        finally:
            db.close()

    def get_events_in_group(self, data):
        """
        Obtiene todos los eventos de un grupo.
        """
        db = self.get_session()
        try:
            return get_events_in_group(db, data["group_id"], data["user_key"])
        finally:
            db.close()

    def get_user_groups(self, data):
        """
        Obtiene todos los grupos de un usuario.
        """
        db = self.get_session()
        try:
            return get_user_groups(db, data["user_key"])
        finally:
            db.close()

    def create_group(self, data):
        """
        Crea un nuevo grupo.
        """
        groupCreate = GroupCreate(name=data['group_name'], hierarchy=data['hierarchy'], creator=data['creator'])
        db = self.get_session()
        try:
            return create_group(db, groupCreate)
        finally:
            db.close()

    def get_group_by_id(self, data):
        """
        Obtiene un grupo por su ID.
        """
        db = self.get_session()
        try:
            return get_group_by_id(db, data["group_id"])
        finally:
            db.close()

    def get_groups(self):
        """
        Obtiene todos los grupos.
        """
        db = self.get_session()
        try:
            return get_groups(db)
        finally:
            db.close()

    def update_group(self, data):
        """
        Actualiza un grupo.
        """
        db = self.get_session()
        try:
            return update_group(db, data["group_id"], data["group_update"])
        finally:
            db.close()

    def delete_group(self, data):
        """
        Elimina un grupo.
        """
        db = self.get_session()
        try:
            return delete_group(db, data["group_id"])
        finally:
            db.close()

    def is_hierarchy_group(self, data):
        """
        Verifica si un grupo es jerárquico.
        """
        db = self.get_session()
        try:
            return is_hierarchy_group(db, data["group_id"])
        finally:
            db.close()

    def get_hierarchy_level(self, data):
        """
        Obtiene el nivel de jerarquía de un usuario en un grupo.
        """
        db = self.get_session()
        try:
            return get_hierarchy_level(db, data["user_key"], data["group_id"])
        finally:
            db.close()

    def get_invited_groups(self, data):
        """
        Obtiene los grupos a los que se está invitando a un usuario.
        """
        db = self.get_session()
        try:
            return get_invited_groups(db, data["user_key"])
        finally:
            db.close()

    def update_hierarchy_level(self, data):
        """
        Modifica el nivel de jerarquía de un usuario en un grupo.
        """
        db = self.get_session()
        try:
            return update_hierarchy_level(db, data["user_key"], data["group_id"], data["new_hierarchy_level"])
        finally:
            db.close()

    def create_event(self, data):
        """
        Crea un nuevo evento.
        """
        db = self.get_session()
        try:
            return create_event(db, data["description"], data["start_time"], data["end_time"], data["state"], data["user_key"])
        finally:
            db.close()

    def get_event_by_id(self, data):
        """
        Obtiene un evento por su ID.
        """
        db = self.get_session()
        try:
            return get_event_by_id(db, data["event_id"])
        finally:
            db.close()

    def get_events(self, data):
        """
        Obtiene todos los eventos de un usuario.
        """
        db = self.get_session()
        try:
            return get_events(db, data["user_key"])
        finally:
            db.close()

    def update_event(self, data):
        """
        Actualiza un evento por su ID.
        """
        db = self.get_session()
        try:
            return update_event(db, data["event_id"], data["new_description"], data["new_start_time"], data["new_end_time"], data["new_state"], data["user_key"])
        finally:
            db.close()

    def delete_event(self, data):
        """
        Elimina un evento por su ID.
        """
        db = self.get_session()
        try:
            return delete_event(db, data["event_id"], data["user_key"])
        finally:
            db.close()

    def get_notifications(self, data):
        """
        Obtiene todas las notificaciones de un usuario.
        """
        db = self.get_session()
        try:
            return get_notifications(db, data["user_key"])
        finally:
            db.close()

    def delete_notification(self, data):
        """
        Elimina una notificación por su ID.
        """
        db = self.get_session()
        try:
            return delete_notification(db, data["notification_id"], data["user_key"])
        finally:
            db.close()