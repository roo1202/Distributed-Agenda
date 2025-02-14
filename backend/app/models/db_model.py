
from event import Event
from group import Group
from meeting import Meeting
from user import User
from group_user_association import association_table
from notification import Notification

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base

def notify_data(data,data_type):
	print(data_type + ": " + data)


class DBModel:
    def __init__(self, id: int):
        # Creamos la URL de conexión de SQLAlchemy
        self.db_name = f"{id}.db"
        self.db_url = f"sqlite:///{self.db_name}"

        self.engine = create_engine(self.db_url, echo=False) 
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        Base.metadata.create_all(self.engine)

    def create_session(self):
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

