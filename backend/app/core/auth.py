from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str


class Authenticator(Protocol):
    async def authenticate(self, request: Request) -> AuthenticatedUser | None: ...


def require_authenticated_user() -> AuthenticatedUser:
    """Phase 1 boundary; replaced by the selected identity/session adapter."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication provider is not configured",
    )

