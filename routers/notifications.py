"""Rotas de notificações. Todas exigem sessão válida."""

from fastapi import APIRouter, Depends, status

from core.deps import get_current_user
from models.user import User
from schemas.notification import NotificationListResponse, NotificationResponse
from services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def list_notifications(current_user: User = Depends(get_current_user)) -> NotificationListResponse:
    return NotificationListResponse(
        notifications=[
            NotificationResponse.from_model(n)
            for n in notification_service.list_for(current_user)
        ],
        unread=notification_service.unread_count(current_user),
    )


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(current_user: User = Depends(get_current_user)) -> None:
    notification_service.mark_all_read(current_user)
