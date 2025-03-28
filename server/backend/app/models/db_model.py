import os
from services.user_service import *
from services.meeting_service import *
from services.group_service import *
from services.event_service import *

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Table, UniqueConstraint, Enum, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

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


Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    text = Column(String, nullable=False)
    time = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="notifications")  
    
    __table_args__ = (UniqueConstraint('user_id', 'id'),)

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    groups = relationship("Group", secondary='group_user_association', back_populates="users")
    meetings = relationship("Meeting", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

association_table = Table(
    'group_user_association',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', BigInteger, ForeignKey('users.id')),
    Column('hierarchy_level', Integer)
)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    hierarchy = Column(Boolean)
    creator = Column(BigInteger, nullable=False)
    users = relationship("User", secondary=association_table, back_populates="groups")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    state = Column(String)
    visibility = Column(String)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    meetings = relationship("Meeting", back_populates="event")

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    state = Column(String)
    event = relationship("Event", back_populates="meetings")
    user = relationship("User", back_populates="meetings")

class DBModel:
    def __init__(self, id: int):
        self.db_name = f"{id}.db"
        self.db_url = f"sqlite:///{self.db_name}"
        self.classes = [User, Group, Event, Meeting, Notification]
        self.tables = [association_table] 

        # Verificar si la base de datos ya existe y eliminarla
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
            print(f"Base de datos existente '{self.db_name}' eliminada.")

        # Verificar si hay copias de bases de datos ya existentes y eliminarlas
        if os.path.exists('copia'+ self.db_name):
            os.remove('copia' + self.db_name)
            print(f"Base de datos existente '{'copia' + self.db_name}' eliminada.")
        
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False)
        
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def filter_function(self, condition, cls):
        def cond(row):
            if cls == Group:
                key = row.creator
            elif cls == User:
                key = row.id
            else:  # Event, Meeting, Notification
                key = row.user_id
            return condition(int(key))
        return cond

    def get_filtered_db(self, condition, new_db_name):
        with self.get_session() as session:
            registers = {cls: session.query(cls).all() for cls in self.classes}
            association_data = session.execute(association_table.select()).fetchall()

        engine_copia = create_engine(f"sqlite:///{new_db_name}", echo=False)
        Base.metadata.create_all(engine_copia)
        
        with sessionmaker(bind=engine_copia)() as session_copia:
            for cls in self.classes:
                filter_cond = self.filter_function(condition, cls)
                for row in registers[cls]:
                    if filter_cond(row):
                        session_copia.merge(cls(**{c.name: getattr(row, c.name) for c in cls.__table__.c}))

            user_ids_in_copy = {user.id for user in session_copia.query(User).all()}
            group_ids_in_copy = {group.id for group in session_copia.query(Group).all()}
            for row in association_data:
                if row.user_id in user_ids_in_copy and row.group_id in group_ids_in_copy:
                    session_copia.execute(
                        association_table.insert().values(
                            user_id=row.user_id,
                            group_id=row.group_id,
                            hierarchy_level=row.hierarchy_level
                        )
                    )
            session_copia.commit()

    def replicate_db(self, db_name):
        engine_origen = create_engine(f"sqlite:///{db_name}", echo=False)
        with sessionmaker(bind=engine_origen)() as session_origen:
            registers = {cls: session_origen.query(cls).all() for cls in self.classes}
            association_data = session_origen.execute(association_table.select()).fetchall()

        with self.get_session() as session_actual:
            for cls in self.classes:
                for row in registers[cls]:
                    session_actual.merge(cls(**{c.name: getattr(row, c.name) for c in cls.__table__.c}))

            for row in association_data:
                session_actual.execute(
                    association_table.insert().values(
                        user_id=row.user_id,
                        group_id=row.group_id,
                        hierarchy_level=row.hierarchy_level
                    )
                )
            session_actual.commit()

    def check_db(self):
        with self.get_session() as session:
            for cls in self.classes:
                notify_data(cls.__name__, "GetData")
                for row in session.query(cls).all():
                    print(f"{cls.__name__}: {row.__dict__}")

            notify_data("group_user_association", "GetData")
            for row in session.execute(association_table.select()).fetchall():
                print(f"Association: user_id={row.user_id}, group_id={row.group_id}, hierarchy_level={row.hierarchy_level}")

    def delete_replicated_db(self, condition):
        with self.get_session() as session:
            association_data = session.execute(association_table.select()).fetchall()
            user_ids_to_delete = {user.id for user in session.query(User).all() if self.filter_function(condition, User)(user)}
            group_ids_to_delete = {group.id for group in session.query(Group).all() if self.filter_function(condition, Group)(group)}
            
            for row in association_data:
                if row.user_id in user_ids_to_delete or row.group_id in group_ids_to_delete:
                    session.execute(
                        association_table.delete().where(
                            (association_table.c.user_id == row.user_id) &
                            (association_table.c.group_id == row.group_id)
                        )
                    )
            for cls in self.classes:
                filter_cond = self.filter_function(condition, cls)
                for row in session.query(cls).all():
                    if filter_cond(row):
                        session.delete(row)
            session.commit()
            notify_data("Replicated data deleted.", 'database')


    # Metodos para el manejo de la base de datos 

    def create_user(self, data):
        """
        Crea un nuevo usuario.
        """
        db = self.get_session()
        try:
            return (create_user(db, data["user_name"], data["user_email"], data["password"])).__json__()
        finally:
            db.close()
                
    def get_user_by_email(self, data):
        """
        Obtiene un usuario por su email.
        """
        db = self.get_session()
        try:
            return (get_user_by_email(db, data["user_email"])).__json__()
        finally:
            db.close()

    def get_user_by_id(self, data):
        """
        Obtiene un usuario por su ID.
        """
        db = self.get_session()
        try:
            user = get_user_by_id(db, data["user_key"])
            if user is not None:
                return user.__json__()
            else:
                return False
        finally:
            db.close()

    def get_users(self, data):
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
            return (update_user(db, data["user_key"], data["new_user_name"])).__json__()
        finally:
            db.close()

    def delete_user(self, data):
        """
        Elimina un usuario por su ID.
        """
        db = self.get_session()
        try:
            return (delete_user(db, data["user_key"])).__json__()
        finally:
            db.close()

    def create_meeting(self, data):
        """
        Crea una nueva reunión.
        """
        db = self.get_session()
        try:
            return (create_meeting(db, data["users_email"], data["state"], data["event_id"], data["user_key"])).__json__()
        finally:
            db.close()

    def create_group_meeting(self, data):
        """
        Crea una nueva reunión de grupo.
        """
        db = self.get_session()
        try:
            return (create_group_meeting(db, data["users_email"], data["state"], data["event_id"], data["user_key"], data["group_id"])).__json__()
        finally:
            db.close()

    def add_meetings(self, data):
        """
        Agrega múltiples reuniones a la base de datos.
        """
        db = self.get_session()
        try:
            return (add_meetings(db, data["meetings"])).__json__()
        finally:
            db.close()

    def get_meeting_by_id(self, data):
        """
        Obtiene una reunión por su ID.
        """
        db = self.get_session()
        try: # ya devuelve un diccionario
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
            return (update_meeting(db, data["meeting_id"], data["new_state"], data["user_key"])).__json__()
        finally:
            db.close()

    def delete_meeting(self, data):
        """
        Elimina una reunión por su ID.
        """
        db = self.get_session()
        try:
            return (delete_meeting(db, data["meeting_id"], data["user_key"])).__json__()
        finally:
            db.close()

    def add_user_to_group(self, data):
        """
        Añade un usuario a un grupo.
        """
        db = self.get_session()
        try:
            return (add_user_to_group(db, data["user_key"], data["group_id"], data.get("hierarchy", 0))).__json__()
        finally:
            db.close()

    def remove_user_from_group(self, data):
        """
        Elimina un usuario de un grupo.
        """
        db = self.get_session()
        try:
            return (remove_user_from_group(db, data["user_key"], data["group_id"])).__json__()
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
            return [event.__json__() for event in get_events_in_group(db, data["group_id"], data["user_key"])]
        finally:
            db.close()

    def get_user_groups(self, data):
        """
        Obtiene todos los grupos de un usuario.
        """
        db = self.get_session()
        try:
            return [group.__json__() for group in get_user_groups(db, data["user_key"])] 
        finally:
            db.close()

    def create_group(self, data):
        """
        Crea un nuevo grupo.
        """
        groupCreate = GroupCreate(name=data['group_name'], hierarchy=data['hierarchy'], creator=data['user_key'])
        db = self.get_session()
        try:
            return (create_group(db, groupCreate)).__json__()
        finally:
            db.close()

    def get_group_by_id(self, data):
        """
        Obtiene un grupo por su ID.
        """
        db = self.get_session()
        try:
            return (get_group_by_id(db, data["group_id"])).__json__()
        finally:
            db.close()

    def get_groups(self, data):
        """
        Obtiene todos los grupos.
        """
        db = self.get_session()
        try:
            return [group.__json__() for group in get_groups(db)] 
        finally:
            db.close()

    def update_group(self, data):
        """
        Actualiza un grupo.
        """
        db = self.get_session()
        try:
            groupUpdate = GroupUpdate(name= data["group_name"], hierarchy=data["group_hierarchy"])
            return (update_group(db, data["group_id"], groupUpdate)).__json__()
        finally:
            db.close()

    def delete_group(self, data):
        """
        Elimina un grupo.
        """
        db = self.get_session()
        try:
            return (delete_group(db, data["user_key"], data["group_id"])).__json__()
        finally:
            db.close()

    def delete_member_group(self, data):
        """
        Elimina un usuario de un grupo.
        """
        db = self.get_session()
        try:
            return (delete_user_group(db, data["user_key"], data["group_id"])).__json__()
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
        try: # ya retorna un int
            return get_hierarchy_level(db, data["user_key"], data["group_id"])
        finally:
            db.close()

    def get_invited_groups(self, data):
        """
        Obtiene los grupos a los que se está invitando a un usuario.
        """
        db = self.get_session()
        try:
            return [group.__json__() for group in get_invited_groups(db, data["user_key"])]
        finally:
            db.close()

    def update_hierarchy_level(self, data):
        """
        Modifica el nivel de jerarquía de un usuario en un grupo.
        """
        db = self.get_session()
        try: # ya devuelve un diccionario
            return update_hierarchy_level(db, data["user_key"], data["group_id"], data["hierarchy"])
        finally:
            db.close()

    def create_event(self, data):
        """
        Crea un nuevo evento.
        """
        db = self.get_session()
        try:
            return (create_event(db, data["description"], data["start_time"], data["end_time"], data["state"], data["user_key"], data["visibility"])).__json__()
        finally:
            db.close()

    def get_event_by_id(self, data):
        """
        Obtiene un evento por su ID.
        """
        db = self.get_session()
        try:
            return (get_event_by_id(db, data["event_id"])).__json__()
        finally:
            db.close()

    def get_events(self, data):
        """
        Obtiene todos los eventos de un usuario.
        """
        db = self.get_session()
        try:
            return [event.__json__() for event in get_events(db, data["user_key"])]
        finally:
            db.close()
    
    def update_event(self, data):
        """
        Actualiza un evento por su ID.
        """
        db = self.get_session()
        try:
            return (update_event(db, data["event_id"], data["new_description"], data["new_start_time"], data["new_end_time"], data["new_state"], data["user_key"], data["visibility"])).__json__()
        finally:
            db.close()

    def delete_event(self, data):
        """
        Elimina un evento por su ID.
        """
        db = self.get_session()
        try:
            return (delete_event(db, data["event_id"], data["user_key"])).__json__()
        finally:
            db.close()

    def get_notifications(self, data):
        """
        Obtiene todas las notificaciones de un usuario.
        """
        db = self.get_session()
        try:
            return [notif.__json__() for notif in get_notifications(db, data["user_key"])]
        finally:
            db.close()

    def delete_notification(self, data):
        """
        Elimina una notificación por su ID.
        """
        db = self.get_session()
        try:
            return (delete_notification(db, data["notification_id"], data["user_key"])).__json__()
        finally:
            db.close()