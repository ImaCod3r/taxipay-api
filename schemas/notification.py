"""Schemas das notificações."""

from pydantic import BaseModel

from models.notification import Notification


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    read: bool
    createdAt: int  # epoch em ms

    @classmethod
    def from_model(cls, n: Notification) -> "NotificationResponse":
        return cls(
            id=str(n.id),
            title=n.title,
            body=n.body,
            read=n.read,
            createdAt=int(n.created_at.timestamp() * 1000),
        )


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    unread: int
