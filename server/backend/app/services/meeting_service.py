from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.meeting import Meeting
from schemas.meeting import MeetingCreate
from models.user import User
from models.event import Event
from services.group_service import get_hierarchy_level
from .user_service import get_user_by_id
from .event_service import get_event_by_id

# Crear una nueva reunion
def create_meeting(db: Session, users_email: list[str], state: str, event_id: int, user_id: int):
    meetings : list[Meeting] = []
    for email in users_email:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{email}' not found")
        else:
            new_meeting = Meeting(
                user_id = user.id,
                state=state,
                event_id = event_id
            )
            meetings.append(new_meeting)

    new_meeting = Meeting(
                user_id = user_id,
                state="Confirmed",
                event_id = event_id
            )

    meetings.append(new_meeting)

    add_meetings(db, meetings)
    
    return new_meeting

# Crear una nueva reunion de grupo
def create_group_meeting(db: Session, users_email: list[str], state: str, event_id: int, user_id: int, group_id: int):
    meetings : list[Meeting] = []
    level = get_hierarchy_level(db, user_id=user_id, group_id=group_id)
    for email in users_email:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{email}' not found")
        else:
            lev = get_hierarchy_level(db, user_id=user.id, group_id=group_id)
            if level > lev and lev > 0 : 
                st = "Confirmed"
            else:
                st = "Pending"
                
            new_meeting = Meeting(
                user_id = user.id,
                state=st,
                event_id = event_id
            )
            meetings.append(new_meeting)

    new_meeting = Meeting(
                user_id = user_id,
                state="Confirmed",
                event_id = event_id
            )

    meetings.append(new_meeting)

    add_meetings(db, meetings)
    
    return new_meeting

def add_meetings(db: Session, meetings: list[Meeting]):
    for meeting in meetings:
        db.add(meeting)
    db.commit()
    for meeting in meetings:
        db.refresh(meeting)
    return meetings

# Obtener una reunion por el id
def get_meeting_by_id(db: Session, meeting_id: int, user_id: int):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    meetings = db.query(Meeting).filter(Meeting.event_id == meeting.event_id).all()
    result = []
    confirmed = True
    cancelled = False
    is_in = False
    for meeting in meetings:
        if meeting.user_id == user_id:
            is_in = True
        user = get_user_by_id(db, meeting.user_id)
        if user:
            result.append(user.email)
            confirmed = confirmed and meeting.state == 'Confirmed'
            cancelled = cancelled or meeting.state == 'Cancelled'

    event = get_event_by_id(db, meeting.event_id)
    state = ''
    if confirmed:
        state = 'Confirmed'
    elif cancelled:
        state = 'Cancelled'
    else:
        state = 'Pending'
    
    return {"state": state,
            "users_email": result,
            "event_id": meeting.event_id,
            "event_description": event.description,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "id": meeting_id,
            "is_in": is_in
            } 


# Obtener todas las reuniones de un usuario
def get_meetings(db: Session, user_id: int): 
    meetings = db.query(Meeting).filter(Meeting.user_id == user_id).all()
    meetings_with_events = []

    for meeting in meetings:
        event = db.query(Event).filter(Event.id == meeting.event_id).first()
        user_email = get_user_by_id(db, event.user_id).email
        meeting_data = {
            "meeting_id": meeting.id,
            "state": meeting.state,
            "event": {
                "event_id": event.id,
                "description": event.description,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "user_email" : user_email
            }
        }
        meetings_with_events.append(meeting_data)

    return meetings_with_events
    

# Actualizar una reunion por ID
def update_meeting(db: Session, meeting_id: int, new_state: str, user_id : int):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if meeting and meeting.user_id == user_id:
        meeting.state = new_state
        db.commit()
        db.refresh(meeting)
    return meeting

# Eliminar una reunion por ID
def delete_meeting(db: Session, meeting_id: int, user_id: int):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if meeting and meeting.user_id == user_id:
        db.delete(meeting)
        db.commit()
    return meeting