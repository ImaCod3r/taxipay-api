"""Regras de negócio da carteira (ledger, saldo, operações)."""

import uuid

from peewee import fn

from core.exceptions import DriverNotFound, InsufficientFunds, InvalidPin
from database.config import db
from models.ledger import Direction, LedgerEntry, LedgerKind
from models.user import Role, User
from services import notification_service

DEFAULT_TX_LIMIT = 50


def _fmt_kz(amount: int) -> str:
    """Formata Kz com separador de milhar (ex.: 1500 -> '1.500 Kz')."""
    return f"{amount:,}".replace(",", ".") + " Kz"


def _sum(user: User, direction: Direction) -> int:
    total = (
        LedgerEntry.select(fn.COALESCE(fn.SUM(LedgerEntry.amount), 0))
        .where((LedgerEntry.user == user) & (LedgerEntry.direction == direction.value))
        .scalar()
    )
    return int(total or 0)


def get_balance(user: User) -> int:
    """Saldo = créditos - débitos. Nunca é guardado; sempre recalculado."""
    return _sum(user, Direction.CREDIT) - _sum(user, Direction.DEBIT)


def list_transactions(user: User, limit: int = DEFAULT_TX_LIMIT) -> list[LedgerEntry]:
    return list(
        LedgerEntry.select()
        .where(LedgerEntry.user == user)
        .order_by(LedgerEntry.created_at.desc(), LedgerEntry.id.desc())
        .limit(limit)
    )


def find_driver_by_code(code: str) -> User | None:
    """Busca um cobrador (DRIVER) pelo código único."""
    return User.get_or_none(
        (User.driver_code == code) & (User.role == Role.DRIVER.value)
    )


def _existing_by_key(user: User, key: str | None) -> LedgerEntry | None:
    """Idempotência: se a mesma chave já foi usada por este usuário, reusa."""
    if not key:
        return None
    return LedgerEntry.get_or_none(
        (LedgerEntry.user == user) & (LedgerEntry.idempotency_key == key)
    )


def deposit(user: User, amount: int, idempotency_key: str | None = None) -> LedgerEntry:
    """Depósito simulado (crédito na conta do passageiro)."""
    with db.atomic():
        existing = _existing_by_key(user, idempotency_key)
        if existing:
            return existing
        return LedgerEntry.create(
            user=user,
            reference=uuid.uuid4().hex,
            kind=LedgerKind.DEPOSIT.value,
            direction=Direction.CREDIT.value,
            amount=amount,
            description="Depósito Multicaixa",
            idempotency_key=idempotency_key,
        )


def withdraw(user: User, amount: int, idempotency_key: str | None = None) -> LedgerEntry:
    """Saque simulado (débito na conta do cobrador)."""
    with db.atomic():
        existing = _existing_by_key(user, idempotency_key)
        if existing:
            return existing
        if get_balance(user) < amount:
            raise InsufficientFunds()
        return LedgerEntry.create(
            user=user,
            reference=uuid.uuid4().hex,
            kind=LedgerKind.WITHDRAWAL.value,
            direction=Direction.DEBIT.value,
            amount=amount,
            description="Saque",
            idempotency_key=idempotency_key,
        )


def pay(
    passenger: User,
    driver_code: str,
    amount: int,
    pin: str,
    idempotency_key: str | None = None,
) -> LedgerEntry:
    """Pagamento: transfere do passageiro para o cobrador (partidas dobradas).

    Exige o PIN do passageiro (validado no servidor).
    Retorna a entrada de débito do passageiro.
    """
    if not passenger.check_pin(pin):
        raise InvalidPin()

    driver = find_driver_by_code(driver_code)
    if driver is None or driver.id == passenger.id:
        raise DriverNotFound()

    with db.atomic():
        existing = _existing_by_key(passenger, idempotency_key)
        if existing:
            return existing
        if get_balance(passenger) < amount:
            raise InsufficientFunds()

        reference = uuid.uuid4().hex
        debit = LedgerEntry.create(
            user=passenger,
            reference=reference,
            kind=LedgerKind.PAYMENT.value,
            direction=Direction.DEBIT.value,
            amount=amount,
            description=f"Pagamento • {driver_code}",
            counterparty=driver_code,
            idempotency_key=idempotency_key,
        )
        LedgerEntry.create(
            user=driver,
            reference=reference,
            kind=LedgerKind.PAYMENT.value,
            direction=Direction.CREDIT.value,
            amount=amount,
            description="Corrida recebida",
            counterparty=passenger.phone,
        )

        # Notifica ambos os lados do pagamento.
        notification_service.create(
            passenger,
            "Pagamento enviado",
            f"Pagaste {_fmt_kz(amount)} a {driver.name}.",
        )
        notification_service.create(
            driver,
            "Pagamento recebido",
            f"Recebeste {_fmt_kz(amount)} de {passenger.name}.",
        )
        return debit
