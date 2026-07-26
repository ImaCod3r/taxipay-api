"""Testes unitários do serviço da carteira (ledger/saldo)."""

import pytest

from core.exceptions import DriverNotFound, InsufficientFunds, InvalidPin
from models.user import Role, User
from services import wallet_service


def _user(phone: str, role: Role, pin: str = "1234", code: str | None = None) -> User:
    user = User(name="Teste", phone=phone, role=role.value, driver_code=code)
    user.set_pin(pin)
    user.save()
    return user


def test_new_user_has_zero_balance():
    passenger = _user("923000001", Role.PASSENGER)
    assert wallet_service.get_balance(passenger) == 0


def test_balance_is_sum_of_entries():
    passenger = _user("923000002", Role.PASSENGER)
    wallet_service.deposit(passenger, 1000)
    wallet_service.deposit(passenger, 500)
    assert wallet_service.get_balance(passenger) == 1500


def test_withdraw_reduces_balance():
    driver = _user("923000003", Role.DRIVER, code="ABC12")
    wallet_service.deposit(driver, 2000)  # crédito inicial para testar saque
    wallet_service.withdraw(driver, 800)
    assert wallet_service.get_balance(driver) == 1200


def test_withdraw_insufficient_raises():
    driver = _user("923000004", Role.DRIVER, code="ABC13")
    with pytest.raises(InsufficientFunds):
        wallet_service.withdraw(driver, 100)


def test_payment_transfers_between_accounts():
    passenger = _user("923000005", Role.PASSENGER)
    driver = _user("923000006", Role.DRIVER, code="DRV99")
    wallet_service.deposit(passenger, 1000)

    wallet_service.pay(passenger, "DRV99", 200, pin="1234")

    assert wallet_service.get_balance(passenger) == 800
    assert wallet_service.get_balance(driver) == 200


def test_payment_wrong_pin_raises():
    passenger = _user("923000007", Role.PASSENGER)
    _user("923000008", Role.DRIVER, code="DRV98")
    wallet_service.deposit(passenger, 1000)
    with pytest.raises(InvalidPin):
        wallet_service.pay(passenger, "DRV98", 200, pin="0000")


def test_payment_unknown_driver_raises():
    passenger = _user("923000009", Role.PASSENGER)
    wallet_service.deposit(passenger, 1000)
    with pytest.raises(DriverNotFound):
        wallet_service.pay(passenger, "ZZZZZ", 200, pin="1234")


def test_payment_insufficient_raises():
    passenger = _user("923000010", Role.PASSENGER)
    _user("923000011", Role.DRIVER, code="DRV97")
    with pytest.raises(InsufficientFunds):
        wallet_service.pay(passenger, "DRV97", 200, pin="1234")


def test_idempotent_deposit_not_duplicated():
    passenger = _user("923000012", Role.PASSENGER)
    wallet_service.deposit(passenger, 500, idempotency_key="dep-1")
    wallet_service.deposit(passenger, 500, idempotency_key="dep-1")  # repetido
    assert wallet_service.get_balance(passenger) == 500


def test_transactions_listed_newest_first():
    passenger = _user("923000013", Role.PASSENGER)
    wallet_service.deposit(passenger, 100)
    wallet_service.deposit(passenger, 200)
    txs = wallet_service.list_transactions(passenger)
    assert len(txs) == 2
    assert txs[0].amount == 200  # mais recente primeiro
