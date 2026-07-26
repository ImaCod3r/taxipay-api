"""Rotas da carteira (Core/Financeiro). Todas exigem sessão válida."""

from fastapi import APIRouter, Depends, HTTPException, status

from core.deps import get_current_user
from core.exceptions import DriverNotFound, InsufficientFunds, InvalidPin
from models.user import Role, User
from schemas.wallet import (
    DepositRequest,
    DriverPublicResponse,
    PayRequest,
    TransactionResponse,
    WalletResponse,
    WithdrawRequest,
)
from services import wallet_service

router = APIRouter(prefix="/wallet", tags=["wallet"])


def _wallet_of(user: User) -> WalletResponse:
    return WalletResponse(
        balance=wallet_service.get_balance(user),
        transactions=[
            TransactionResponse.from_entry(entry)
            for entry in wallet_service.list_transactions(user)
        ],
    )


def _require_role(user: User, role: Role) -> None:
    if user.role != role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação não permitida para este perfil.",
        )


@router.get("", response_model=WalletResponse)
def get_wallet(current_user: User = Depends(get_current_user)) -> WalletResponse:
    return _wallet_of(current_user)


@router.get("/driver/{code}", response_model=DriverPublicResponse)
def find_driver(code: str, _: User = Depends(get_current_user)) -> DriverPublicResponse:
    driver = wallet_service.find_driver_by_code(code.strip().upper())
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cobrador não encontrado."
        )
    return DriverPublicResponse(driver_code=driver.driver_code, name=driver.name)


@router.post("/deposit", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def deposit(data: DepositRequest, current_user: User = Depends(get_current_user)) -> WalletResponse:
    _require_role(current_user, Role.PASSENGER)
    wallet_service.deposit(current_user, data.amount, data.idempotency_key)
    return _wallet_of(current_user)


@router.post("/withdraw", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def withdraw(data: WithdrawRequest, current_user: User = Depends(get_current_user)) -> WalletResponse:
    _require_role(current_user, Role.DRIVER)
    try:
        wallet_service.withdraw(current_user, data.amount, data.idempotency_key)
    except InsufficientFunds as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    return _wallet_of(current_user)


@router.post("/pay", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def pay(data: PayRequest, current_user: User = Depends(get_current_user)) -> WalletResponse:
    _require_role(current_user, Role.PASSENGER)
    try:
        wallet_service.pay(
            current_user, data.driver_code, data.amount, data.pin, data.idempotency_key
        )
    except InvalidPin as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))
    except DriverNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except InsufficientFunds as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    return _wallet_of(current_user)
