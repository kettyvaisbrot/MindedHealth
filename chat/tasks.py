import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from .models import ChatMessage, PseudonymAssignment
from .services import ROOM_NAME_BY_ROLE, get_chat_day

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def end_chat_day():
    """Runs daily at 23:59 Asia/Jerusalem (see CELERY_BEAT_SCHEDULE).

    For every chat room: deletes today's messages and pseudonym assignments,
    and force-disconnects anyone currently connected (close code 4000)."""
    chat_day = get_chat_day()
    channel_layer = get_channel_layer()

    for room_name in ROOM_NAME_BY_ROLE.values():
        logger.info("end_chat_day: starting cleanup for room=%s chat_day=%s", room_name, chat_day)

        deleted_messages, _ = ChatMessage.objects.filter(
            room_name=room_name, chat_day=chat_day
        ).delete()
        deleted_pseudonyms, _ = PseudonymAssignment.objects.filter(
            room_name=room_name, chat_day=chat_day
        ).delete()

        async_to_sync(channel_layer.group_send)(
            f"chat_{room_name}",
            {"type": "day_ended"},
        )

        logger.info(
            "end_chat_day: room=%s done -- deleted %d messages, %d pseudonym assignments",
            room_name,
            deleted_messages,
            deleted_pseudonyms,
        )
