from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.event import Event
from schemas.event import EventCreate
from models.meeting import Meeting

# Crear un nuevo evento
def create_event(db: Session, description: str, start_time, end_time, state: str, user_id: int, visibility: str):
    new_event = Event(
        description=description,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        state=state,
        user_id=user_id,
        visibility=visibility
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
    return db.query(Event).filter(Event.user_id == user_id).all()

# Actualizar un evento por ID
def update_event(db: Session, event_id: int, new_description: str, new_start_time, new_end_time, new_state: str, user_id: int, visibility:str):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event and user_id == event.user_id:
        event.description = new_description
        event.start_time = datetime.fromisoformat(new_start_time)
        event.end_time = datetime.fromisoformat(new_end_time)
        event.state = new_state
        event.visibility = visibility
        db.commit()
        db.refresh(event)
    return event

# Eliminar un evento por ID
def delete_event(db: Session, event_id: int, user_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event and event.user_id == user_id:
        # Eliminar todas las reuniones asociadas al evento
        db.query(Meeting).filter(Meeting.event_id == event_id).delete()
        
        # Eliminar el evento
        db.delete(event)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Event not found or not authorized")
    return event