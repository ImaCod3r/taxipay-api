class AppError(Exception):
    """Base para erros de regra de negócio."""

class PhoneAlreadyRegistered(AppError):
    def __init__(self) -> None:
        super().__init__("Este número já está cadastrado.")


class InvalidCredentials(AppError):
    def __init__(self) -> None:
        super().__init__("Número ou PIN incorretos.")


class InsufficientFunds(AppError):
    def __init__(self) -> None:
        super().__init__("Saldo insuficiente.")


class DriverNotFound(AppError):
    def __init__(self) -> None:
        super().__init__("Cobrador não encontrado.")


class InvalidPin(AppError):
    def __init__(self) -> None:
        super().__init__("PIN incorreto.")


class ForbiddenOperation(AppError):
    def __init__(self, message: str = "Operação não permitida para este perfil.") -> None:
        super().__init__(message)