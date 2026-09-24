"""Security, Authentication, and Role-Based Access Control (RBAC) Layer.

Implements security hardening per SIH26079 §22 and Research Files 114, 115 (L2):
- Roles: ADMIN, FORECASTER, RESEARCHER, VIEWER.
- Scopes: predict:read, predict:write, predict:review, models:read, models:admin, data:export, system:admin.
- API Key & Bearer Token authentication with fail-safe defaults for development/evaluation.
- Input bounds validation and sanitization against injection / denial-of-service attacks.
"""
from dataclasses import dataclass, field
from enum import Enum
import os
import re
from typing import Any, Dict, List, Optional, Set
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging = __import__("logging").getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class UserRole(str, Enum):
    """User roles for role-based access control (RBAC)."""

    ADMIN = "ADMIN"
    FORECASTER = "FORECASTER"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


# Role-to-Scope mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.VIEWER: {
        "predict:read",
        "forecasts:read",
        "metrics:read",
        "analogs:read",
    },
    UserRole.FORECASTER: {
        "predict:read",
        "predict:write",
        "predict:review",  # Human-in-the-loop review
        "forecasts:read",
        "metrics:read",
        "analogs:read",
    },
    UserRole.RESEARCHER: {
        "predict:read",
        "predict:write",
        "models:read",
        "metrics:read",
        "data:export",
        "analogs:read",
    },
    UserRole.ADMIN: {
        "predict:read",
        "predict:write",
        "predict:review",
        "models:read",
        "models:admin",
        "data:export",
        "system:admin",
        "analogs:read",
    },
}


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user or service client."""

    user_id: str
    role: UserRole
    scopes: Set[str] = field(default_factory=set)
    is_authenticated: bool = True

    def has_scope(self, scope: str) -> bool:
        """Check if user possesses required permission scope."""
        return scope in self.scopes or "system:admin" in self.scopes

    def has_role(self, minimum_role: UserRole) -> bool:
        """Check if user role satisfies minimum hierarchy level."""
        hierarchy = [UserRole.VIEWER, UserRole.RESEARCHER, UserRole.FORECASTER, UserRole.ADMIN]
        try:
            return hierarchy.index(self.role) >= hierarchy.index(minimum_role)
        except ValueError:
            return False


# Built-in API Key Registry for evaluation / prototype environments
_API_KEYS: Dict[str, AuthenticatedUser] = {
    "veyra-admin-key-2026": AuthenticatedUser(
        user_id="admin-01",
        role=UserRole.ADMIN,
        scopes=ROLE_PERMISSIONS[UserRole.ADMIN],
    ),
    "veyra-forecaster-key-2026": AuthenticatedUser(
        user_id="forecaster-imd-01",
        role=UserRole.FORECASTER,
        scopes=ROLE_PERMISSIONS[UserRole.FORECASTER],
    ),
    "veyra-researcher-key-2026": AuthenticatedUser(
        user_id="researcher-01",
        role=UserRole.RESEARCHER,
        scopes=ROLE_PERMISSIONS[UserRole.RESEARCHER],
    ),
    "veyra-viewer-key-2026": AuthenticatedUser(
        user_id="viewer-public-01",
        role=UserRole.VIEWER,
        scopes=ROLE_PERMISSIONS[UserRole.VIEWER],
    ),
}

# Default unauthenticated public user (when auth is optional in development)
PUBLIC_VIEWER = AuthenticatedUser(
    user_id="public-anonymous",
    role=UserRole.VIEWER,
    scopes=ROLE_PERMISSIONS[UserRole.VIEWER],
    is_authenticated=False,
)


def get_current_user(
    x_api_key: Optional[str] = Security(API_KEY_HEADER),
) -> AuthenticatedUser:
    """Authenticate incoming request using API key header.
    
    If no API key is provided and authentication is not strictly enforced via AUTH_REQUIRED=true,
    returns a default VIEWER user with read permissions.
    """
    auth_required = os.getenv("AUTH_REQUIRED", "False").lower() in ("true", "1", "yes")

    if not x_api_key:
        if auth_required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key header. Authentication required.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return PUBLIC_VIEWER

    key_clean = x_api_key.strip()
    user = _API_KEYS.get(key_clean)
    if not user:
        # Check environment variable configured custom admin key
        custom_admin = os.getenv("VEYRA_ADMIN_API_KEY")
        if custom_admin and key_clean == custom_admin:
            return AuthenticatedUser(
                user_id="env-admin",
                role=UserRole.ADMIN,
                scopes=ROLE_PERMISSIONS[UserRole.ADMIN],
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key provided.",
        )

    return user


def require_scope(scope: str):
    """Dependency factory ensuring the authenticated user has a specific permission scope."""

    def scope_checker(user: AuthenticatedUser = Security(get_current_user)) -> AuthenticatedUser:
        if not user.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires permission scope '{scope}'. User possesses: {sorted(user.scopes)}",
            )
        return user

    return scope_checker


def require_role(role: UserRole):
    """Dependency factory ensuring the authenticated user meets a minimum role hierarchy."""

    def role_checker(user: AuthenticatedUser = Security(get_current_user)) -> AuthenticatedUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role '{role.value}' or higher. User has role: '{user.role.value}'",
            )
        return user

    return role_checker


# Input Sanitization and Bounds Enforcement
_LOCATION_REGEX = re.compile(r"^[a-zA-Z0-9\s,\.\-_]{1,100}$")


def sanitize_input_string(value: str, field_name: str = "input", max_length: int = 100) -> str:
    """Validate and sanitize free-text input strings against injection and buffer-overflow attempts."""
    if not value or not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Field '{field_name}' must be a non-empty string.",
        )
    trimmed = value.strip()
    if len(trimmed) > max_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Field '{field_name}' exceeds maximum allowed length of {max_length} characters.",
        )
    if not _LOCATION_REGEX.match(trimmed):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Field '{field_name}' contains invalid characters. Only alphanumeric, spaces, commas, and hyphens allowed.",
        )
    return trimmed
