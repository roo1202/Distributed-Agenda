from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.meetings import Meeting
from app.schemas.meeting import MeetingCreate
from app.models.user import User
from .user_service import get_user_by_id

# Crear una nueva reunion
def create_meeting(db: Session, users_email: list[str], state: str, event_id: int, user_id: int):
    meetings : list[Meeting] = []
    for user in users_email:
        user = db.query(User).filter(User.email == user).first()
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{user}' not found")
        else:
            new_meeting = Meeting(
                user_id = user.id,
                state=state,
                event_id = event_id
            )
            meetings.append(new_meeting)

    new_meeting = Meeting(
                user_id = user_id,
                state=state,
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
def get_meeting_by_id(db: Session, meeting_id: int):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    meetings = db.query(Meeting).filter(Meeting.event_id == meeting.event_id).all()
    result = []
    confirmed = True
    cancelled = False
    for meeting in meetings:
        user = get_user_by_id(db, meeting.user_id)
        if user:
            result.append(user.email)
            confirmed = confirmed and meeting.state == 'confirmed'
            cancelled = cancelled or meeting.state == 'cancelled'

    state = ''
    if confirmed:
        state = 'confirmed'
    elif cancelled:
        state = 'cancelled'
    else:
        state = 'pending'
    
    meeting.state = state
    db.commit()
    db.refresh(meeting)
    return (state, result, meeting.event_id)



# Obtener todas las reuniones de un usuario
def get_meetings(db: Session, user_id: int): 
    return db.query(Meeting).filter(Meeting.user_id == user_id)

# Actualizar una reunion por ID
def update_meeting(db: Session, meeting_id: int, new_event_id: int, new_state: str):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if meeting:
        meeting.event_id = new_event_id
        meeting.state = new_state
        db.commit()
        db.refresh(meeting)
    return meeting

# Eliminar una reunion por ID
def delete_meeting(db: Session, meeting_id: int):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if meeting:
        db.delete(meeting)
        db.commit()
    return meeting