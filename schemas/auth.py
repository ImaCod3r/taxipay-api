import re

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from models.user import Role

_PHONE_RE = re.compile(r"^9\d{8}$")
_PIN_RE = re.compile(r"^\d{4}$")


class RegisterRequest(BaseModel):
    name: str
    phone: str
    pin: str
    role: Role

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Digita o teu nome completo.")
        return value

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not _PHONE_RE.match(value):
            raise ValueError("Número inválido. Use 9 dígitos começando por 9.")
        return value

    @field_validator("pin")
    @classmethod
    def _validate_pin(cls, value: str) -> str:
        if not _PIN_RE.match(value):
            raise ValueError("O PIN deve ter exatamente 4 dígitos.")
        return value

class LoginRequest(BaseModel):
    phone: str
    pin: str


class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str

    @field_validator("current_pin", "new_pin")
    @classmethod
    def _validate_pin(cls, value: str) -> str:
        if not _PIN_RE.match(value):
            raise ValueError("O PIN deve ter exatamente 4 dígitos.")
        return value

    @model_validator(mode="after")
    def _pins_differ(self) -> "ChangePinRequest":
        if self.current_pin == self.new_pin:
            raise ValueError("O novo PIN deve ser diferente do atual.")
        return self


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    role: Role
    driver_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(UserResponse):
    """Resposta de login/registo.

    A web autentica pelo cookie HttpOnly e nunca recebe ``token`` — mantendo o
    JWT fora do alcance do JavaScript (resistente a XSS). O app mobile não tem
    cookie jar fiável, por isso pede o token com o header ``X-Client: mobile``,
    guarda-o no keystore e envia-o em ``Authorization: Bearer``
    (ver ``core.deps._extract_token``).
    """

    token: str | None = None