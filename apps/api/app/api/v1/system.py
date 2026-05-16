from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.models import User
from app.schemas import SystemSafetySettingsResponse


READ_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/safety-settings", response_model=SystemSafetySettingsResponse)
def get_safety_settings(
    _current_user: User = Depends(require_roles(*READ_ROLES)),
) -> SystemSafetySettingsResponse:
    return SystemSafetySettingsResponse(
        external_ai_enabled=False,
        equipment_control_enabled=False,
        interlock_bypass_allowed=False,
        output_forcing_allowed=False,
        human_approval_required=True,
        audit_logging_enabled=True,
        deterministic_engine_enabled=True,
        allowed_equipment_scope=["Load Port", "FOUP Clamp", "EtherCAT I/O"],
        policy_version="PR-20-read-only-safety-boundary-v1",
        generated_at=datetime.now(UTC),
    )
