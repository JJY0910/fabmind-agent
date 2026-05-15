from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel


RoleCode = Literal["FIELD_ENGINEER", "SENIOR_ENGINEER", "ADMIN"]


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str
    role: RoleCode
    tenant_id: uuid.UUID


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser

