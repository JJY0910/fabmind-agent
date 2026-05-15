from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.audit import router as audit_router
from app.api.v1.diagnosis_sessions import router as diagnosis_sessions_router
from app.api.v1.equipment import router as equipment_router
from app.api.v1.health import router as health_router

app = FastAPI(title="FabMind Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(diagnosis_sessions_router, prefix="/api/v1")
app.include_router(equipment_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
