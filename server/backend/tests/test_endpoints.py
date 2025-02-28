# test_endpoints.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.group import Group
from app.models.group_user_association import association_table

# Configurar la base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_endpoints.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear las tablas de la base de datos
Base.metadata.create_all(bind=engine)

# Sobrescribir la dependencia de la base de datos
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)

def get_access_token(test_client):
    # Crear un usuario
    response = test_client.post("/auth/register", json={"name": "John Doe", "email": "johndoe@example.com", "password": "password123"})
    assert response.status_code == 200

    # Obtener un token de acceso
    response = test_client.post("/auth/token", data={"username": "johndoe@example.com", "password": "password123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token

def test_create_user(test_client):
    token = get_access_token(test_client)
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.post("/users/", json={"name": "Jane Doe", "email": "janedoe@example.com", "password": "password123"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "janedoe@example.com"

def test_get_users(test_client):
    token = get_access_token(test_client)
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get("/users/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user_by_email(test_client):
    token = get_access_token(test_client)
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get("/users/janedoe@example.com", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "janedoe@example.com"

def test_delete_user(test_client):
    token = get_access_token(test_client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Crear un usuario para eliminar
    response = test_client.post("/users/", json={"name": "Jane Doe", "email": "janedoe@example.com", "password": "password123"}, headers=headers)
    user_id = response.json()["id"]

    # Eliminar el usuario
    response = test_client.delete(f"/users/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "janedoe@example.com"

    # Verificar que el usuario ha sido eliminado
    response = test_client.get(f"/users/{user_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"