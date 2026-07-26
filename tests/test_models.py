"""Testes do model User."""

import pytest
from peewee import IntegrityError

from models.user import Role, User


def _make_user(**overrides) -> User:
    data = {"name": "Ana", "phone": "923456789", "role": Role.PASSENGER.value}
    data.update(overrides)
    user = User(**data)
    user.set_pin(overrides.get("pin", "1234"))
    user.save()
    return user


def test_set_pin_stores_hash_not_plaintext():
    user = _make_user()
    assert user.pin_hash != "1234"
    assert user.pin_hash.startswith("pbkdf2_sha256$")


def test_check_pin():
    user = _make_user()
    assert user.check_pin("1234") is True
    assert user.check_pin("9999") is False


def test_phone_must_be_unique():
    _make_user(phone="923456789")
    with pytest.raises(IntegrityError):
        _make_user(phone="923456789")


def test_role_is_persisted():
    user = _make_user(phone="912000000", role=Role.DRIVER.value)
    reloaded = User.get_by_id(user.id)
    assert reloaded.role == "DRIVER"
