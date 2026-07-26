"""Dependências reutilizáveis de autenticação."""

import jwt
from fastapi import HTTPException, Request, status

from core.config import COOKIE_NAME
from core.tokens import decode_access_token
from models.user import User

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sessão inválida ou expirada.",
)


def _extract_token(request: Request) -> str | None:
    """Token do cookie HttpOnly; se ausente, do header Authorization (mobile)."""
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer ") :]
    return None


def get_current_user(request: Request) -> User:
    """Valida a sessão (cookie/token) e devolve o usuário autenticado."""
    token = _extract_token(request)
    if not token:
        raise _UNAUTHORIZED
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _UNAUTHORIZED

    user = User.get_or_none(User.id == user_id)
    if user is None:
        raise _UNAUTHORIZED
    return user
