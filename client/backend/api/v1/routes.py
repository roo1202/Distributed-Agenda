from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from schemas.notification import NotifResponse
from services.user_service import *
from schemas.user import UserCreate, UserResponse, UserBase
from schemas.event import EventPrivate, EventResponse, EventBase, EventCreate
from schemas.group import GroupBase, GroupCreate, GroupUpdate, GroupResponse
from services.event_service import *
from schemas.meeting import *
from services.meeting_service import *
from services.group_service import *
from auth import oauth2_scheme, SECRET_KEY, ALGORITHM
from schemas.auth import TokenData
from client import Client

router = APIRouter()

def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    client:Client = request.app.state.client  
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
    user = client.get_user_by_email(user_email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

############## USERS #######################

# Crear un usuario
@router.post("/users/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, request: Request):
    client:Client = request.app.state.client  
    create = client.create_account(user.email, user.name, user.password)
    if create :
        return UserResponse(create, name=user.name, email=user.email)          
    else:
        raise HTTPException(status_code=400, detail="User already exists")

# Eliminar un usuario por su id
@router.delete("/users/", response_model=UserBase)
def delete_user_endpoint(request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    user = client.delete_user(user["id"])
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Obtener un usuario por su email
@router.get("/users/{user_email}", response_model=UserResponse)
def get_user_endpoint(user_email: str, request: Request):
    client:Client = request.app.state.client  
    user = client.get_user_by_email(user_email)
    if user is None:
        return UserResponse(email="User %s not found" % user_email, id= 0)
    return user


################### EVENTS ###########################

# Crear un nuevo evento a un usuario
@router.post("/events/user/", response_model=EventResponse)
def create_event_endpoint(event: EventCreate, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    event = client.create_event(event_name=event.description, date_initial=event.start_time.isoformat(), date_end=event.end_time.isoformat(), privacity=event.visibility , state=event.state, user_key=user["id"])
    return event

# Obtener los eventos del propio usuario
@router.get("/events/user/", response_model=List[EventResponse])
def get_events_endpoint(request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    events = client.get_events(user["id"])
    events_list = []
    for event in events:
        event["start_time"] = datetime.fromisoformat(event["start_time"])
        event["end_time"] = datetime.fromisoformat(event["end_time"])
    events_list = list(events)
    return events_list

# Obtener los eventos de un usuario por su email
@router.get("/events/user/email/", response_model=List[EventBase])
def get_events_endpoint(request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    events = client.get_events(user["id"])
    events_list = []
    for event in events:
        event["start_time"] = datetime.fromisoformat(event["start_time"])
        event["end_time"] = datetime.fromisoformat(event["end_time"])
    events_list = list(events)
    return events_list
    

# Elimina un evento por su id
@router.delete("/events/{event_id}", response_model=EventBase)
def delete_event_endpoint(event_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    event = client.delete_event(event_id, user["id"])
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Actualizar la informacion de un evento
@router.put("/events/{event_id}", response_model=EventResponse)
def update_event_endpoint(event_id:int, event: EventCreate, request: Request, user= Depends(get_current_user)):
    client:Client = request.app.state.client  
    event = client.update_event(event_id=event_id, new_description= event.description, new_start_time=event.start_time.isoformat(), new_end_time = event.end_time.isoformat(), new_state= event.state, user_id = user["id"], visibility= event.visibility)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

################# MEETINGS #############################

# Crear una reunion desde un usuario
@router.post("/meetings/user/", response_model=MeetingBase)
def create_meeting_endpoint(meeting: MeetingCreate, request: Request, user: User = Depends(get_current_user)):
    client:Client = request.app.state.client  
    meeting = client.create_meeting(users_email= meeting.users_email, state= meeting.state, event_id= meeting.event_id, user_id=user["id"])
    if meeting is None:
        raise HTTPException(status_code=404, detail="Create meeting fail")
    return meeting

# Obtener todas las reuniones de un usuario
@router.get("/meetings/user/", response_model=List[MeetingResponse])
def get_meetings_endpoint( request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    meetings = client.get_meetings(user["id"])
    meetings_info = [{"state": meeting["state"], 
                      "id" : meeting["meeting_id"], 
                      "event_description": meeting["event"]["description"],
                      "start_time": datetime.fromisoformat(meeting["event"]["start_time"]),
                      "end_time": datetime.fromisoformat(meeting["event"]["end_time"])
                      } for meeting in meetings ]

    return list(meetings_info)

# Obtener toda la informacion de una reunion por su id
@router.get("/meetings/{meeting_id}", response_model=MeetingInfo)
def get_meeting_endpoint(meeting_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    meeting_data = client.get_meeting_by_id(meeting_id, user["id"])
    if meeting_data is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting_data["start_time"] = datetime.fromisoformat(meeting_data["start_time"])
    meeting_data["end_time"] = datetime.fromisoformat(meeting_data["end_time"])
    return meeting_data
        

# Eliminar una reunion
@router.delete("/meetings/{meeting_id}", response_model=MeetingResponse)
def delete_meeting_endpoint(meeting_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    meeting = client.delete_meeting(meeting_id, user["id"])
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

# Actualizar una reunion
@router.post("/meetings/{meeting_id}", response_model=MeetingBase)
def update_meeting_endpoint(meeting_id:int, meeting: MeetingBase, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    meeting = client.update_meeting(meeting_id=meeting_id, new_state= meeting.state, user_id=user["id"])
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


################### GROUPS ##########################

# Actualizar el nivel de jerarquia de un usuario
@router.put("/groups/{group_id}/users/{user_id}/hierarchy/{hierarchy}")
def update_hierarchy_level_endpoint(group_id: int, user_id: int, hierarchy: int, request: Request, current_user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    current_user_hierarchy = client.get_hierarchy_level(current_user["id"], group_id)
    if int(current_user_hierarchy) >= hierarchy and client.update_hierarchy_level(user_id, group_id, hierarchy) is not None:
        return True
    else:
        raise HTTPException(status_code=404, detail="Update denied")

# Aceptar la invitacion a un grupo
@router.put("/groups/{group_id}/users/me")
def accept_group_invitation_endpoint(group_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    user_hierarchy = client.get_hierarchy_level(user["id"], group_id)
    if int(user_hierarchy) >= 1000 and client.update_hierarchy_level(user["id"], group_id, user_hierarchy - 1000) is not None:
        return True
    else:
        raise HTTPException(status_code=404, detail="Failed acceptance")
    
    
# Crear un nuevo grupo
@router.post("/groups/hierarchy/{hierarchy}", response_model=GroupResponse)
def create_group_endpoint(group: GroupBase, request: Request, user = Depends(get_current_user), hierarchy:int = 0):
    client:Client = request.app.state.client  
    group = client.create_group(group_name=group.name, group_type=group.hierarchy, creator=user["id"])
    if group is not None:
        member = client.add_user_to_group(user["id"], group["id"], hierarchy - 1000)
        if member is not None:
            return group
        raise HTTPException(status_code=404, detail="Failed adding member")
    raise HTTPException(status_code=404, detail="Failed creating group")
    

# Obtener un grupo por su ID
@router.get("/groups/group_id/{group_id}", response_model=GroupResponse)
def get_group_by_id_endpoint(group_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    group = client.get_group_by_id(user["id"], group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Actualizar un grupo
@router.put("/groups/group_id/{group_id}", response_model=GroupResponse)
def update_group_endpoint(group_id: int, group_update: GroupBase, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    group = client.update_group(user["id"], group_id, new_group_name= group_update.name, new_group_hierarchy= group_update.hierarchy)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Eliminar un grupo
@router.delete("/groups/group_id/{group_id}", response_model=GroupResponse)
def delete_group_endpoint(group_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    group = client.delete_group(user["id"], group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Añadir un usuario a un grupo
@router.post("/groups/{group_id}/users/{user_email}/level/{hierarchy}", response_model=GroupResponse)
def add_user_to_group_endpoint(group_id: int, hierarchy: int, user_email:str, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    groups = [group["id"] for group in client.get_user_groups(user["id"])]
    if len(groups)>0 and group_id in groups:
        user = client.get_user_by_email(user_email)
        if user is None:
            raise HTTPException(status_code=404, detail="The user you are trying to add does not exist.")
        group = client.add_user_to_group(user["id"], group_id, hierarchy)
    else:
        raise HTTPException(status_code=404, detail="You do not have permission to add an user to this group.")
    return group

# Eliminar un usuario de un grupo
@router.delete("/groups/{group_id}/users/{user_email}", response_model=GroupResponse)
def remove_user_from_group_endpoint(user_email : str, group_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    groups = [group["id"] for group in client.get_user_groups(user["id"])]
    user_to_remove = client.get_user_by_email(user_email)
    if user_to_remove is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_to_remove_h = client.get_hierarchy_level(user_to_remove["id"], group_id)
    user_actual_h = client.get_hierarchy_level(user["id"], group_id)
    if group_id in groups and user_to_remove is not None and user_to_remove_h is not None and user_actual_h is not None and int(user_to_remove_h) <= int(user_actual_h):
        group = client.remove_user_from_group(user_to_remove["id"], group_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")
    else :
        raise HTTPException(status_code=404, detail="Your hierarchy is lower than the user hierarchy")
    return group

# Obtener todos los grupos de un usuario
@router.get("/groups/users", response_model=List[GroupResponse])
def get_user_groups_endpoint(request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    groups = client.get_user_groups(user["id"])
    return list(groups)

# Obtener todos los usuarios que pertenecen a un grupo
@router.get("/groups/{group_id}/users", response_model=List[str])
def get_users_in_group_endpoint(group_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    user_emails = client.get_users_in_group(user["id"], group_id)
    if not user_emails : #or user["email"] not in user_emails
        raise HTTPException(status_code=404, detail="Group not found or no users in group")
    return user_emails

# Obtener todos los eventos de un grupo
@router.get("/groups/{group_id}/events", response_model=List[EventBase])
def get_events_in_group_endpoint(group_id: int, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    events = client.get_events_in_group(group_id, user["id"])
    if not events:
        raise HTTPException(status_code=404, detail="Group not found or no events in group")
    return events

# Crear una reunion con miembros del grupo
@router.post("/groups/{group_id}/meetings/user/", response_model=MeetingBase)
def create_group_meeting_endpoint(group_id: int, meeting: MeetingCreate, request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    meeting = client.create_group_meeting(users_email= meeting.users_email, state=meeting.state, event_id= meeting.event_id, user_id=user["id"], group_id=group_id)
    if meeting is not None:
        return meeting
    raise HTTPException(status_code=404, detail="Creating meeting in group fail")

# Obtener los grupos a los que se me esta invitando
@router.get("/groups/users/invited_groups", response_model=List[GroupResponse])
def get_invited_groups_endpoint(request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    groups = client.get_invited_groups(user["id"])
    return list(groups)
    

#################### NOTIFICATIONS ###########################################

# Obtener todas las notificaciones de un usuario
@router.get("/notifications/user", response_model=List[NotifResponse])
def get_notifications_endpoint(request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    notif = client.get_notifications(user["id"])
    return list(notif)

# Eliminar una notificacion por su id
@router.delete("/notifications/{notif_id}")
def delete_notification_endpoint(notif_id : int ,request: Request, user = Depends(get_current_user)):
    client:Client = request.app.state.client  
    notif = client.delete_notification(notif_id, user["id"])
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif