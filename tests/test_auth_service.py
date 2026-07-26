"""Testes das regras de negócio de autenticação."""

import pytest

from core.exceptions import InvalidCredentials, PhoneAlreadyRegistered
from schemas.auth import LoginRequest, RegisterRequest
from services import auth_service


def _register(**overrides):
    data = {"name": "Ana Silva", "phone": "923456789", "pin": "1234", "role": "PASSENGER"}
    data.update(overrides)
    return auth_service.register_user(RegisterRequest(**data))


def test_register_user_hashes_pin():
    user = _register()
    assert user.id is not None
    assert user.pin_hash != "1234"
    assert user.check_pin("1234")


def test_register_duplicate_phone_raises():
    _register()
    with pytest.raises(PhoneAlreadyRegistered):
        _register(name="Outro")


def test_authenticate_success():
    _register()
    user = auth_service.authenticate_user(LoginRequest(phone="923456789", pin="1234"))
    assert user.phone == "923456789"


def test_authenticate_wrong_pin_raises():
    _register()
    with pytest.raises(InvalidCredentials):
        auth_service.authenticate_user(LoginRequest(phone="923456789", pin="0000"))


def test_authenticate_unknown_phone_raises():
    with pytest.raises(InvalidCredentials):
        auth_service.authenticate_user(LoginRequest(phone="999999999", pin="1234"))
