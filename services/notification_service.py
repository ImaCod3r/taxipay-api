"""Regras das notificações do usuário."""

from models.notification import Notification
from models.user import User

DEFAULT_LIMIT = 50


def create(user: User, title: str, body: str) -> Notification:
    """Cria uma notificação para um usuário."""
    return Notification.create(user=user, title=title, body=body)


def list_for(user: User, limit: int = DEFAULT_LIMIT) -> list[Notification]:
    """Últimas notificações do usuário (mais recentes primeiro)."""
    return list(
        Notification.select()
        .where(Notification.user == user)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
    )


def unread_count(user: User) -> int:
    return (
        Notification.select()
        .where((Notification.user == user) & (Notification.read == False))  # noqa: E712
        .count()
    )


def mark_all_read(user: User) -> None:
    (
        Notification.update(read=True)
        .where((Notification.user == user) & (Notification.read == False))  # noqa: E712
        .execute()
    )
