import hashlib
from sqlalchemy.orm import Session
from models.user import User
from models.notification import Notification
from schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_key(key: str) -> int:
    """
    Función de hash que calcula el hash SHA-1 de una cadena de caracteres y devuelve un número entero que se utiliza como la clave del nodo en la red Chord.
    """
    sha1 = hashlib.sha1(key.encode('utf-8'))
    hash_value = int(sha1.hexdigest(), 16) 
    string_num = str(hash_value)
    new_string = string_num[:16]
    return int(new_string)

# Crear un nuevo usuario
def create_user(db: Session, name: str, email: str, password: str):
    hashed_password = get_password_hash(password)
    new_user = User(id=hash_key(email) ,name=name, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Obtener un usuario por su email
def get_user_by_email(db: Session, user_email: str):
    return db.query(User).filter(User.email == user_email).first()

# Obtener un usuario por su id
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# Obtener todos los usuarios
def get_users(db: Session): 
    return db.query(User).all()

# Actualizar un usuario por ID
def update_user(db: Session, user_id: int, new_name: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.name = new_name
        db.commit()
        db.refresh(user)
    return user

# Eliminar un usuario por ID
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user


# Obtiene las notificaciones de un usuario
def get_notifications(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user.notifications
    return []

# Eliminar una notificacion por ID
def delete_notification(db: Session, notification_id:int, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if user and notification and notification.user_id == user_id:
        db.delete(notification)
        db.commit()
    return notification