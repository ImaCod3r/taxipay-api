"""Schemas da carteira (entrada/saída)."""

import re

from pydantic import BaseModel, Field, field_validator

from models.ledger import Direction, LedgerEntry

_PIN_RE = re.compile(r"^\d{4}$")
_MAX_AMOUNT = 10_000_000  # teto de sanidade (Kz)


class DepositRequest(BaseModel):
    amount: int = Field(gt=0, le=_MAX_AMOUNT)
    idempotency_key: str | None = None


class WithdrawRequest(BaseModel):
    amount: int = Field(gt=0, le=_MAX_AMOUNT)
    idempotency_key: str | None = None


class PayRequest(BaseModel):
    driver_code: str
    amount: int = Field(gt=0, le=_MAX_AMOUNT)
    pin: str
    idempotency_key: str | None = None

    @field_validator("driver_code")
    @classmethod
    def _norm_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("pin")
    @classmethod
    def _validate_pin(cls, value: str) -> str:
        if not _PIN_RE.match(value):
            raise ValueError("O PIN deve ter 4 dígitos.")
        return value


class TransactionResponse(BaseModel):
    id: str
    type: str
    direction: str  # "in" | "out"
    amount: int
    description: str
    createdAt: int  # epoch em ms

    @classmethod
    def from_entry(cls, entry: LedgerEntry) -> "TransactionResponse":
        return cls(
            id=str(entry.id),
            type=entry.kind,
            direction="in" if entry.direction == Direction.CREDIT.value else "out",
            amount=entry.amount,
            description=entry.description,
            createdAt=int(entry.created_at.timestamp() * 1000),
        )


class WalletResponse(BaseModel):
    balance: int
    transactions: list[TransactionResponse]


class DriverPublicResponse(BaseModel):
    """Dados públicos de um cobrador (para o passageiro confirmar antes de pagar)."""

    driver_code: str
    name: str
