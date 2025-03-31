
from fastapi import HTTPException
from sqlalchemy import delete, insert, select, update, and_
from sqlalchemy.orm import Session
from models.group import Group
from schemas.group import GroupCreate, GroupUpdate
from models.user import User
from models.group_user_association import association_table
from models.event import Event

# Añadir un usuario a un grupo
def add_user_to_group(db: Session, user_id: int, group_id: int, hierarchy_level: int = 0):
    user = db.query(User).filter(User.id == user_id).first()
    group = db.query(Group).filter(Group.id == group_id).first()
    if user and group:
        stmt = insert(association_table).values(group_id=group_id, user_id=user_id, hierarchy_level=hierarchy_level + 1000)
        db.execute(stmt)
        db.commit()
    return group

# Servicio para eliminar un usuario de un grupo
def remove_user_from_group(db: Session, user_id: int, group_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    group = db.query(Group).filter(Group.id == group_id).first()
    if user and group:
        group.users.remove(user)
        db.commit()
    return group

# Obtener todos los usuarios que pertenecen a un grupo por su id
def get_users_in_group(db: Session, group_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return []
    
    user_emails = []
    for user in group.users:
        hierarchy_level = db.execute(
            select(association_table.c.hierarchy_level)
            .where(association_table.c.user_id == user.id)
            .where(association_table.c.group_id == group_id)
        ).fetchone()
        
        if hierarchy_level and hierarchy_level[0] < 1000:
            user_emails.append(user.email)
    
    return user_emails

# Obtener todos los eventos de un grupo por su id
def get_events_in_group(db: Session, group_id: int, user_id: int):
    user_in_group = db.execute(
        select(association_table.c.user_id)
        .where(association_table.c.group_id == group_id)
        .where(association_table.c.user_id == user_id)
    ).fetchone()

    if not user_in_group:
        raise HTTPException(status_code=403, detail="User does not belong to the group")

    users_in_group = db.execute(
        select(association_table.c.user_id)
        .where(association_table.c.group_id == group_id)
        .where(association_table.c.hierarchy_level <= 1000)
    ).fetchall()

    user_ids = [user.user_id for user in users_in_group]

    events = db.query(Event).filter(Event.user_id.in_(user_ids)).all()

    return [event for event in events]

# Obtener todos los grupos de un usuario
def get_user_groups(db: Session, user_id: int):
    groups = db.query(Group).join(
        association_table,
        and_(
            association_table.c.group_id == Group.id,
            association_table.c.user_id == user_id,
            association_table.c.hierarchy_level < 1000
        )
    ).all()
    
    if groups :
        return groups
    return []

# Servicio para crear un grupo
def create_group(db: Session, group: GroupCreate):
    new_group = Group(
        name=group.name,
        hierarchy=group.hierarchy,
        creator = group.creator
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

# Servicio para obtener un grupo por su ID
def get_group_by_id(db: Session, group_id: int):
    return db.query(Group).filter(Group.id == group_id).first()

# Servicio para obtener todos los grupos
def get_groups(db: Session):
    return db.query(Group).all()

# Servicio para actualizar un grupo
def update_group(db: Session, group_id: int, group_update: GroupUpdate):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group:
        group.name = group_update.name
        group.hierarchy = group_update.hierarchy
        db.commit()
        db.refresh(group)
    return group

# Servicio para eliminar un grupo
def delete_group(db: Session, user_id: int, group_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group:
        if group.creator == user_id:
            db.delete(group)
            db.commit()
        else:
            remove_user_from_group(db, user_id, group_id)
    return group

# Servicio para eliminar un usuario de un grupo
def delete_user_group(db: Session, user_id: int, group_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group:
        stmt = delete(association_table).where(
        (association_table.c.user_id == user_id) &
        (association_table.c.group_id == group_id))
    
        db.execute(stmt)
        db.commit()
    return group

# Servicio para saber si un grupo es jerarquico
def is_hierarchy_group(db: Session, group_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group:
        return group.hierarchy
    raise HTTPException(status_code=403, detail="Group not found")

# Servicio para obtener el nivel de jerarquía de un usuario en un grupo
def get_hierarchy_level(db: Session, user_id: int, group_id: int) -> int:
    result = db.execute(
        select(association_table.c.hierarchy_level)
        .where(association_table.c.user_id == user_id)
        .where(association_table.c.group_id == group_id)
    ).fetchone()

    if result:
        return result[0]
    else:
        raise HTTPException(status_code=404, detail="Hierarchy level not found")
    
# Servicio para obtener los grupos a los que se me esta invitando
def get_invited_groups(db: Session, user_id: int):
    groups = db.execute(
        select(Group) 
        .join(association_table, Group.id == association_table.c.group_id)
        .where(association_table.c.user_id == user_id)
        .where(association_table.c.hierarchy_level >= 1000)
    ).scalars().all()
    return groups


# Servicio para modificar el nivel de jerarquia en un grupo
def update_hierarchy_level(db: Session, user_id: int, group_id: int, new_hierarchy_level: int):
    stmt = update(association_table).where(
        (association_table.c.user_id == user_id) &
        (association_table.c.group_id == group_id)
    ).values(hierarchy_level=new_hierarchy_level)
    db.execute(stmt)
    db.commit()
    return {"message": "Hierarchy level updated"}
    