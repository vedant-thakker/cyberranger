from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router, target_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Authenticate target client against local DVWA container
    target_client.authenticate()
    yield
    # Shutdown: Trigger emergency stop on guard to halt all pending threads
    target_client.guard.trigger_emergency_stop()


app = FastAPI(
    title="CyberRanger API",
    description="Autonomous Cybersecurity Test Generation and Detection Research Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "CyberRanger Backend",
        "docs": "/docs",
        "api_health": "/api/health",
        "target_endpoint": "http://127.0.0.1:8080",
    }
