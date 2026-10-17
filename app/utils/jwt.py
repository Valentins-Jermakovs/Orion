# ==============================
# Standard library imports
# ==============================

from typing import Any

# ==============================
# Third-party imports
# ==============================

import jwt


# ==============================
# JWT manager
# ==============================

class JWTManager:
    """Validate access tokens issued by the authentication service."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
    ) -> None:
        """Initialize JWT validation settings."""
        self.secret_key = secret_key
        self.algorithm = algorithm

    def validate_access_token(self, token: str) -> dict[str, Any]:
        """Validate an access token and return its payload."""
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={
                "require": ["exp", "sub", "type"],
            },
        )

        # Accept access tokens only.
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Invalid token type.")

        return payload
