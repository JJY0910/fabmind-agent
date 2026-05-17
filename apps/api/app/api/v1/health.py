from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "fabmind-agent-api"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {
        "status": "ready",
        "service": "fabmind-agent-api",
        "database": "ok",
        "external_ai_enabled": False,
        "equipment_control_enabled": False,
        "read_only_diagnostics": True,
    }
