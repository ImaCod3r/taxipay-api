"""Rotas de autenticação (camada HTTP)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from core.cookies import clear_auth_cookie, set_auth_cookie
from core.deps import get_current_user
from core.exceptions import InvalidCredentials, InvalidPin, PhoneAlreadyRegistered
from core.tokens import create_access_token
from models.user import User
from schemas.auth import ChangePinRequest, LoginRequest, RegisterRequest, UserResponse
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _start_session(response: Response, user: User) -> UserResponse:
    """Emite o JWT num cookie HttpOnly e devolve os dados do usuário."""
    token = create_access_token(subject=str(user.id), role=user.role)
    set_auth_cookie(response, token)
    return UserResponse.model_validate(user)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, response: Response) -> UserResponse:
    try:
        user = auth_service.register_user(data)
    except PhoneAlreadyRegistered as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return _start_session(response, user)


@router.post("/login", response_model=UserResponse)
def login(data: LoginRequest, response: Response) -> UserResponse:
    try:
        user = auth_service.authenticate_user(data)
    except InvalidCredentials as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))
    return _start_session(response, user)


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
