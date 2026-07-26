"""Testes do hashing de PIN."""

from core.security import hash_pin, verify_pin


def test_hash_is_not_plaintext():
    hashed = hash_pin("1234")
    assert hashed != "1234"
    assert hashed.startswith("pbkdf2_sha256$")


def test_same_pin_produces_different_hashes():
    # Salt aleatório => hashes distintos para o mesmo PIN.
    assert hash_pin("1234") != hash_pin("1234")


def test_verify_correct_pin():
    assert verify_pin("1234", hash_pin("1234")) is True


def test_verify_wrong_pin():
    assert verify_pin("0000", hash_pin("1234")) is False


def test_verify_malformed_hash_is_false():
    assert verify_pin("1234", "nao-e-um-hash") is False
    assert verify_pin("1234", "") is False
