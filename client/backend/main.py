from fastapi import FastAPI
from api.v1.routess.auth import router as auth_router
from api.v1.routes import router as api_router
from client import Client
import uvicorn

app = FastAPI()

# Crear una instancia de Client
client = Client()

# Incluir las rutas de los endpoints
app.include_router(auth_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")

# Pasar la instancia de Client a los routers
app.state.client = client

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)