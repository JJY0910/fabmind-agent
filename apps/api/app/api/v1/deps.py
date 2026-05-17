from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.services.audit import create_audit_event


ROLE_FIELD = "FIELD_ENGINEER"
ROLE_SENIOR = "SENIOR_ENGINEER"
ROLE_ADMIN = "ADMIN"

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
        token_tenant_id = UUID(payload["tenant_id"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from None

    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id, User.is_active.is_(True)))
    if user is None or user.tenant_id != token_tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str) -> Callable[[Request, CurrentUser, Session], User]:
    def dependency(request: Request, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> User:
        role_code = current_user.role.code
        if role_code not in allowed_roles:
            create_audit_event(
                db,
                tenant_id=current_user.tenant_id,
                actor_user_id=current_user.id,
                event_type="RBAC_PERMISSION_DENIED",
                resource_type="api_route",
                severity="SECURITY",
                payload={
                    "path": request.url.path,
                    "method": request.method,
                    "role": role_code,
                    "allowed_roles": list(allowed_roles),
                    "path_params": {key: str(value) for key, value in request.path_params.items()},
                },
            )
            db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency
