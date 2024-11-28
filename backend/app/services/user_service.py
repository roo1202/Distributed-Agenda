from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

# Crear un nuevo usuario
def create_user(db: Session, name: str, email: str, password: str):
    fake_hashed_password = f"{password}hashed"  # Simulación de hashing
    new_user = User(name=name, email=email, hashed_password=fake_hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

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