"""Rotas de autenticação (camada HTTP)."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from core.cookies import clear_auth_cookie, set_auth_cookie
from core.deps import get_current_user
from core.exceptions import InvalidCredentials, InvalidPin, PhoneAlreadyRegistered
from core.tokens import create_access_token
from models.user import User
from schemas.auth import (
    ChangePinRequest,
    LoginRequest,
    RegisterRequest,
    SessionResponse,
    UserResponse,
)
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _wants_token(request: Request) -> bool:
    """Só clientes sem cookie jar (mobile) recebem o JWT no corpo."""
    return request.headers.get("X-Client", "").lower() == "mobile"


def _start_session(request: Request, response: Response, user: User) -> SessionResponse:
    """Emite o JWT no cookie HttpOnly; devolve-o no corpo só para o mobile."""
    token = create_access_token(subject=str(user.id), role=user.role)
    set_auth_cookie(response, token)
    return SessionResponse(
        **UserResponse.model_validate(user).model_dump(),
        token=token if _wants_token(request) else None,
    )


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, request: Request, response: Response) -> SessionResponse:
    try:
        user = auth_service.register_user(data)
    except PhoneAlreadyRegistered as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return _start_session(request, response, user)


@router.post("/login", response_model=SessionResponse)
def login(data: LoginRequest, request: Request, response: Response) -> SessionResponse:
    try:
        user = auth_service.authenticate_user(data)
    except InvalidCredentials as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))
    return _start_session(request, response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_auth_cookie(response)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/change-pin", status_code=status.HTTP_204_NO_CONTENT)
def change_pin(data: ChangePinRequest, current_user: User = Depends(get_current_user)) -> None:
    try:
        auth_service.change_pin(current_user, data.current_pin, data.new_pin)
    except InvalidPin as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))
