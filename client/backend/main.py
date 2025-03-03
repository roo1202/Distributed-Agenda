from fastapi import FastAPI
from api.v1.routess.auth import router as auth_router
from api.v1.routes import router as api_router
from .client import Client
import os

app = FastAPI()

# Obtener IP y puerto de las variables de entorno
client_ip = os.getenv("CLIENT_IP", "0.0.0.0")
client_port = int(os.getenv("CLIENT_PORT", 8000))

# Crear una instancia de Client con IP y puerto dinámicos
client = Client(my_address=(client_ip, client_port))

# Incluir las rutas de los endpoints
app.include_router(auth_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")

# Pasar la instancia de Client a los routers
app.state.client = client