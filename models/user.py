from datetime import datetime
from enum import Enum

from peewee import CharField, DateTimeField

from core.security import hash_pin, verify_pin
from database.config import BaseModel

class Role(str, Enum):
    """Perfil do usuário — espelha o tipo do frontend."""

    PASSENGER = "PASSENGER"
    DRIVER = "DRIVER"

class User(BaseModel):
    name = CharField()
    phone = CharField(unique=True, index=True)
    pin_hash = CharField()
    role = CharField(choices=[(r.value, r.value) for r in Role])
    # Código único do cobrador (só DRIVER). Usado para receber pagamentos.
    driver_code = CharField(null=True, unique=True, index=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "users"

    def set_pin(self, raw_pin: str) -> None:
        """Define o PIN a partir do texto puro, guardando só o hash."""
        self.pin_hash = hash_pin(raw_pin)

    def check_pin(self, raw_pin: str) -> bool:
        """Confere um PIN em texto puro contra o hash guardado."""
        return verify_pin(raw_pin, self.pin_hash)
