"""Criação e validação de tokens JWT."""

from datetime import datetime, timedelta, timezone

import jwt

from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY


def create_access_token(subject: str, role: str) -> str:
    """Gera um JWT de acesso para o usuário (subject = id)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Valida o JWT e retorna o payload. Levanta ``jwt.PyJWTError`` se inválido."""
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
