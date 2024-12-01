from datetime import datetime
from sqlalchemy.orm import Session
from app.models.event import Event
from app.schemas.event import EventCreate

# Crear un nuevo evento
def create_event(db: Session, description: str, start_time: datetime, end_time: datetime, state: str, user_id: int):
    new_event = Event(
        description=description,
        start_time=start_time,
        end_time=end_time,
        state=state,
        user_id=user_id
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

# Obtener un evento por su id
def get_event_by_id(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()

# Obtener todos los eventos de un usuario
def get_events(db: Session, user_id: int): 
    return db.query(Event).filter(Event.user_id == user_id)

# Actualizar un evento por ID
def update_event(db: Session, event_id: int, new_description: str, new_start_time: datetime, new_end_time: datetime, new_state: str, user_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event and user_id == event.user_id:
        event.description = new_description
        event.start_time = new_start_time
        event.end_time = new_end_time
        event.state = new_state
        db.commit()
        db.refresh(event)
    return event

# Eliminar un evento por ID
def delete_event(db: Session, event_id: int, user_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event and event.user_id == user_id:
        db.delete(event)
        db.commit()
    return event