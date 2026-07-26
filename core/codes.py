"""Geração de códigos únicos de cobrador (ex.: "UNK3O")."""

import secrets

# Sem caracteres ambíguos (0/O, 1/I).
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_LENGTH = 5


def generate_driver_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_LENGTH))
