"""Testes de criação e validação de JWT."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core.config import JWT_ALGORITHM, SECRET_KEY
from core.tokens import create_access_token, decode_access_token


def test_roundtrip_carries_claims():
    token = create_access_token(subject="42", role="DRIVER")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "DRIVER"
    assert "exp" in payload and "iat" in payload


def test_tampered_token_is_rejected():
    token = create_access_token(subject="1", role="PASSENGER")
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_expired_token_is_rejected():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    expired = jwt.encode({"sub": "1", "exp": past}, SECRET_KEY, algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)


def test_wrong_secret_is_rejected():
    forged = jwt.encode({"sub": "1"}, "outra-chave-de-assinatura-completamente-diferente", algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(forged)
