from typing import List
from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.user_service import *
from app.schemas.user import UserCreate, UserResponse, UserBase
from app.db.session import SessionLocal
from app.schemas.event import EventResponse, EventBase, EventCreate
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.services.event_service import *
from app.schemas.meeting import *
from app.services.meeting_service import *
from app.services.group_service import *
from app.auth import oauth2_scheme, SECRET_KEY, ALGORITHM
from app.schemas.auth import TokenData

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, user_email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

############## USERS #######################

# Crear un usuario
@router.post("/users/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user.name, user.email, user.password)

# Obtener todos los usuarios
@router.get("/users/", response_model=List[UserBase])
def get_users_endpoint(db: Session = Depends(get_db)):
    return get_users(db)

# Eliminar un usuario por su id
@router.delete("/users/", response_model=UserBase)
def delete_user_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user = delete_user(db, user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Obtener un usuario por su email
@router.get("/users/{user_email}", response_model=UserResponse)
def get_user_endpoint(user_email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, user_email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


################### EVENTS ###########################

# Crear un nuevo evento a un usuario
@router.post("/events/user/", response_model=EventResponse)
def create_event_endpoint(event: EventCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_event(db, description=event.description, start_time=event.start_time, end_time=event.end_time, state=event.state, user_id=user.id)

# Obtener los eventos de un usuario por su id
@router.get("/events/user/", response_model=List[EventResponse])
def get_events_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_events(db, user.id)

# Elimina un evento por su id
@router.delete("/events/{event_id}", response_model=EventBase)
def delete_event_endpoint(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = delete_event(db, event_id, user.id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Actualizar la informacion de un evento
@router.put("/events/{event_id}", response_model=EventResponse)
def update_event_endpoint(event_id:int, event: EventCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return update_event(db, event_id=event_id, new_description= event.description, new_start_time=event.start_time, new_end_time = event.end_time, new_state= event.state, user_id = user.id)


################# MEETINGS #############################

# Crear una reunion desde un usuario
@router.post("/meetings/user/", response_model=MeetingResponse)
def create_meeting_endpoint(meeting: MeetingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_meeting(db, users_email= meeting.users_email, state= meeting.state, event_id= meeting.event_id, user_id=user.id)

# Obtener todas las reuniones de un usuario
@router.get("/meetings/user/", response_model=List[MeetingResponse])
def get_meetings_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_meetings(db, user.id)

# Obtener toda la informacion de una reunion por su id
@router.get("/meetings/{meeting_id}", response_model=MeetingCreate)
def get_meeting_endpoint(meeting_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meeting_data = get_meeting_by_id(db, meeting_id, user.id)
    if meeting_data[3]:
        return MeetingCreate(state=meeting_data[0], users_email=meeting_data[1],event_id=meeting_data[2])
    else:
        raise HTTPException(status_code=404, detail="Access denied")

# Eliminar una reunion
@router.delete("/meetings/{meeting_id}", response_model=MeetingResponse)
def delete_meeting_endpoint(meeting_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meeting = delete_meeting(db, meeting_id, user.id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

# Actualizar una reunion
@router.post("/meetings/{meeting_id}", response_model=MeetingResponse)
def update_meeting_endpoint(meeting_id:int, meeting: MeetingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return update_meeting(db, meeting_id=meeting_id, new_event_id= meeting.event_id, new_state= meeting.state, user_id=user.id)


################### GROUPS ##########################

# Crear un nuevo grupo
@router.post("/groups/", response_model=GroupResponse)
def create_group_endpoint(group: GroupCreate, db: Session = Depends(get_db)):
    return create_group(db, group)

# Obtener un grupo por su ID
@router.get("/groups/{group_id}", response_model=GroupResponse)
def get_group_by_id_endpoint(group_id: int, db: Session = Depends(get_db)):
    group = get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Obtener todos los grupos
@router.get("/groups/", response_model=List[GroupResponse])
def get_groups_endpoint(db: Session = Depends(get_db)):
    return get_groups(db)

# Actualizar un grupo
@router.put("/groups/{group_id}", response_model=GroupResponse)
def update_group_endpoint(group_id: int, group_update: GroupUpdate, db: Session = Depends(get_db)):
    group = update_group(db, group_id, group_update)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Eliminar un grupo
@router.delete("/groups/{group_id}", response_model=GroupResponse)
def delete_group_endpoint(group_id: int, db: Session = Depends(get_db)):
    group = delete_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Añadir un usuario a un grupo
@router.post("/groups/{group_id}/user/", response_model=GroupResponse)
def add_user_to_group_endpoint(group_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group = add_user_to_group(db, user.id, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group or User not found")
    return group

# Eliminar un usuario de un grupo
@router.delete("/groups/{group_id}/user/", response_model=GroupResponse)
def remove_user_from_group_endpoint(group_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group = remove_user_from_group(db, user.id, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group or User not found")
    return group

# Obtener todos los grupos de un usuario
@router.get("/users/groups", response_model=List[GroupResponse])
def get_user_groups_endpoint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    groups = get_user_groups(db, user.id)
    if not groups:
        raise HTTPException(status_code=404, detail="User not found or no groups")
    return groups

# Obtener todos los usuarios que pertenecen a un grupo
@router.get("/groups/{group_id}/users", response_model=List[str])
def get_users_in_group_endpoint(group_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_emails = get_users_in_group(db, group_id)
    if not user_emails or user.email not in user_emails:
        raise HTTPException(status_code=404, detail="Group not found or no users in group")
    return user_emails