from core.codes import generate_driver_code
from core.exceptions import InvalidCredentials, InvalidPin, PhoneAlreadyRegistered
from models.user import Role, User
from schemas.auth import LoginRequest, RegisterRequest


def _unique_driver_code() -> str:
    for _ in range(10):
        code = generate_driver_code()
        if not User.select().where(User.driver_code == code).exists():
            return code
    raise RuntimeError("Não foi possível gerar um código de cobrador único.")


def register_user(data: RegisterRequest) -> User:
    """Cria um usuário com o PIN criptografado.

    Levanta ``PhoneAlreadyRegistered`` se o número já existir.
    Cobradores (DRIVER) recebem um código único para receber pagamentos.
    """
    if User.select().where(User.phone == data.phone).exists():
        raise PhoneAlreadyRegistered()

    driver_code = _unique_driver_code() if data.role == Role.DRIVER else None
    user = User(
        name=data.name,
        phone=data.phone,
        role=data.role.value,
        driver_code=driver_code,
    )
    user.set_pin(data.pin)
    user.save()
    return user

def authenticate_user(data: LoginRequest) -> User:
    """Valida número + PIN e retorna o usuário.

    Levanta ``InvalidCredentials`` se o número não existir ou o PIN não bater.
    """
    user = User.get_or_none(User.phone == data.phone)
    if user is None or not user.check_pin(data.pin):
        raise InvalidCredentials()
    return user


def change_pin(user: User, current_pin: str, new_pin: str) -> None:
    """Troca o PIN após validar o PIN atual.

    Levanta ``InvalidPin`` se o PIN atual não bater.
    """
    if not user.check_pin(current_pin):
        raise InvalidPin()
    user.set_pin(new_pin)
    user.save()