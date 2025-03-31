from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.routess.auth import router as auth_router
from api.v1.routes import router as api_router
from client import Client
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

# Crear una instancia de Client
client = Client()

# Incluir las rutas de los endpoints
app.include_router(auth_router, prefix="/auth")
app.include_router(api_router, prefix="/api/v1")

# Pasar la instancia de Client a los routers
app.state.client = client

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)