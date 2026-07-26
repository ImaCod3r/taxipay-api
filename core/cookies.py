"""Gestão do cookie de autenticação (HttpOnly)."""

from typing import Literal, cast

from fastapi import Response

from core.config import (
    COOKIE_DOMAIN,
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
)

_SameSite = Literal["lax", "strict", "none"]


def set_auth_cookie(response: Response, token: str) -> None:
    """Grava o JWT num cookie HttpOnly seguro."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=cast(_SameSite, COOKIE_SAMESITE),
        domain=COOKIE_DOMAIN,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Remove o cookie de autenticação (logout)."""
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=cast(_SameSite, COOKIE_SAMESITE),
        domain=COOKIE_DOMAIN,
        path="/",
    )
