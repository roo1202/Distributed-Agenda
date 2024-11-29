from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.user_service import *
from app.schemas.user import UserCreate, UserResponse, UserBase
from app.db.session import SessionLocal
from app.schemas.event import EventResponse, EventBase, EventCreate
from app.services.event_service import *
from app.schemas.meeting import *
from app.services.meeting_service import *

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user.name, user.email, user.password)


@router.get("/users/", response_model=List[UserBase])
def get_users_endpoint(db: Session = Depends(get_db)):
    return get_users(db)


@router.delete("/users/{user_id}", response_model=UserBase)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    user = delete_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{user_email}", response_model=UserResponse)
def get_user_endpoint(user_email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, user_email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


################### EVENTS ###########################

@router.post("/events/user/{user_id}", response_model=EventResponse)
def create_event_endpoint(user_id: int ,event: EventCreate, db: Session = Depends(get_db)):
    return create_event(db, description=event.description, start_time=event.start_time, end_time=event.end_time, state=event.state, user_id=user_id)


@router.get("/events/user/{user_id}", response_model=List[EventResponse])
def get_events_endpoint(user_id: int, db: Session = Depends(get_db)):
    return get_events(db, user_id)


@router.delete("/events/{event_id}", response_model=EventBase)
def delete_event_endpoint(event_id: int, db: Session = Depends(get_db)):
    event = delete_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/events/{event_id}", response_model=EventResponse)
def update_event_endpoint(event_id:int, event: EventCreate, db: Session = Depends(get_db)):
    return update_event(db, event_id=event_id, new_description= event.description, new_start_time=event.start_time, new_end_time = event.end_time, new_state= event.state)


################# MEETINGS #############################

# Crear una reunion desde un usuario
@router.post("/meetings/user/{user_id}", response_model=MeetingResponse)
def create_meeting_endpoint(user_id: int ,meeting: MeetingCreate, db: Session = Depends(get_db)):
    return create_meeting(db, users_email= meeting.users_email, state= meeting.state, event_id= meeting.event_id, user_id=user_id)

# Obtener todas las reuniones de un usuario
@router.get("/meetings/user/{user_id}", response_model=List[MeetingResponse])
def get_meetings_endpoint(user_id: int, db: Session = Depends(get_db)):
    return get_meetings(db, user_id)

# Obtener toda la informacion de una reunion por su id
@router.get("/meetings/{meeting_id}", response_model=MeetingCreate)
def get_meeting_endpoint(meeting_id: int, db: Session = Depends(get_db)):
    meeting_data = get_meeting_by_id(db, meeting_id)
    return MeetingCreate(state=meeting_data[0], users_email=meeting_data[1],event_id=meeting_data[2])

# Eliminar una reunion
@router.delete("/meetings/{meeting_id}", response_model=MeetingResponse)
def delete_meeting_endpoint(meeting_id: int, db: Session = Depends(get_db)):
    meeting = delete_meeting(db, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

# Actualizar una reunion
@router.post("/meetings/{meeting_id}", response_model=MeetingResponse)
def update_meeting_endpoint(meeting_id:int, meeting: MeetingUpdate, db: Session = Depends(get_db)):
    return update_meeting(db, meeting_id=meeting_id, new_event_id= meeting.event_id, new_state= meeting.state)

