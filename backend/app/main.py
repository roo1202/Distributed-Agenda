from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as api_router
from app.api.v1.routess.auth import router as auth_router


app = FastAPI()

# Define the origins that should be allowed to make requests to your API
origins = [
    "http://localhost:3000",  # Adjust this to match your frontend's URL
    "http://127.0.0.1:3000",
]

# Add the CORS middleware to your FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/auth")


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}