from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import CurrentUser
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models import Tenant, User
from app.schemas import AuthUser, LoginRequest, LoginResponse
from app.services.audit import create_audit_event


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.username == payload.username, User.is_active.is_(True))
        .limit(1)
    )

    if user is None or not verify_password(payload.password, user.password_hash):
        tenant_id = user.tenant_id if user is not None else _fallback_tenant_id(db)
        if tenant_id is not None:
            create_audit_event(
                db,
                tenant_id=tenant_id,
                actor_user_id=user.id if user is not None else None,
                event_type="AUTH_LOGIN_FAILURE",
                resource_type="auth",
                severity="SECURITY",
                payload={"username": payload.username},
            )
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role_code=user.role.code)
    create_audit_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        event_type="AUTH_LOGIN_SUCCESS",
        resource_type="auth",
        severity="INFO",
        payload={"username": user.username, "role": user.role.code},
    )
    db.commit()

    return LoginResponse(
        access_token=token,
        user=_auth_user(user),
    )


@router.get("/me", response_model=AuthUser)
def me(current_user: CurrentUser) -> AuthUser:
    return _auth_user(current_user)


def _auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role.code,
        tenant_id=user.tenant_id,
    )


def _fallback_tenant_id(db: Session):
    return db.scalar(select(Tenant.id).where(Tenant.code == "FABMIND_DEMO")) or db.scalar(select(Tenant.id).limit(1))

