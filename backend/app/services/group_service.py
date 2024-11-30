from sqlalchemy.orm import Session
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate
from app.models.user import User

# Añadir un usuario a un grupo
def add_user_to_group(db: Session, user_id: int, group_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    group = db.query(Group).filter(Group.id == group_id).first()
    if user and group:
        group.users.append(user)
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
        user_emails.append(user.email)
    
    return user_emails

# Obtener todos los grupos de un usuario
def get_user_groups(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user.groups
    return []

# Servicio para crear un grupo
def create_group(db: Session, group: GroupCreate):
    new_group = Group(
        name=group.name,
        hierarchy=group.hierarchy
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
def delete_group(db: Session, group_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group:
        db.delete(group)
        db.commit()
    return group