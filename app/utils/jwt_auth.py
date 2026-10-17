
# ==============================
# Standard library imports
# ==============================

from collections.abc import Callable
from typing import Any

# ==============================
# Third-party imports
# ==============================

import jwt

from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

# ==============================
# Application imports
# ==============================

from app.utils.jwt import JWTManager


# ==============================
# Authentication configuration
# ==============================

bearer_scheme = HTTPBearer(auto_error=False)


# ==============================
# JWT authentication
# ==============================

class JWTAuth:
    """Provide JWT authentication and role-based authorization."""

    def __init__(self, jwt_manager: JWTManager) -> None:
        """Initialize authentication dependencies."""
        self.jwt_manager = jwt_manager

    async def get_current_user(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(
            bearer_scheme
        ),
    ) -> dict[str, Any]:
        """Validate the access token and return its payload."""
        # Reuse a token already validated by the authentication middleware.
        payload = getattr(request.state, "current_user", None)

        if payload is not None:
            return payload

        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = self.jwt_manager.validate_access_token(
                credentials.credentials
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

        request.state.current_user = payload
        return payload

    def require_roles(
        self,
        roles: list[str],
    ) -> Callable[..., Any]:
        """Create a dependency that requires at least one specified role."""

        async def dependency(
            payload: dict[str, Any] = Depends(self.get_current_user),
        ) -> dict[str, Any]:
            """Check whether the user has a required role."""
            user_roles = payload.get("roles", [])

            if not isinstance(user_roles, list) or not any(
                role in user_roles for role in roles
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden",
                )

            return payload

        return dependency
