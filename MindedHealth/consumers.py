import json
import html
import logging
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from collections import defaultdict
from django.utils import timezone as django_timezone

from chat.models import ChatMessage, ModerationLog
from chat.moderation import contains_profanity
from chat.services import CHAT_TIMEZONE, get_chat_day, get_history_page, get_or_create_pseudonym, get_room_name_for_user

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 500  # characters
RATE_LIMIT_SECONDS = 1  # 1 message per second per user

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Secure ChatConsumer with:
    - Authentication checks
    - HTML/JS escaping
    - Per-room user tracking
    - Logging & rate limiting
    - Optional content filtering
    - Message length limit
    """

    rooms_users = {}  # connected users per room
    user_last_message_time = defaultdict(lambda: 0)  # timestamp of last message per user

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Authentication check
        if not self.scope["user"].is_authenticated:
            await self.close(code=4001)  # unauthorized
            return

        # Role -> room enforcement. This is the real security boundary: a raw
        # WebSocket connection never goes through the `room` HTTP view, so the
        # room name in the URL can't be trusted just because it looks right --
        # a client could open a socket straight to /ws/chat/patient/ regardless
        # of their actual role.
        if get_room_name_for_user(self.scope["user"]) != self.room_name:
            await self.close(code=4003)  # forbidden
            return

        # Auto-generated, day-stable display name -- never the real username.
        self.pseudonym = await database_sync_to_async(get_or_create_pseudonym)(
            self.scope["user"], self.room_name
        )

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.room_group_name not in ChatConsumer.rooms_users:
            ChatConsumer.rooms_users[self.room_group_name] = {}

        ChatConsumer.rooms_users[self.room_group_name][self.channel_name] = self.pseudonym
        await self.send(text_data=json.dumps({"type": "your_pseudonym", "pseudonym": self.pseudonym}))

        messages, has_more = await database_sync_to_async(get_history_page)(self.room_name)
        await self.send(text_data=json.dumps({"type": "history", "messages": messages, "has_more": has_more}))

        await self.send_user_list()

    async def disconnect(self, close_code):
        if self.room_group_name in ChatConsumer.rooms_users:
            ChatConsumer.rooms_users[self.room_group_name].pop(self.channel_name, None)

        await self.send_user_list()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # Internal-only identity, for rate limiting and server logs -- never sent to any client.
        real_user_key = self.scope["user"].username
        now = time.time()

        try:
            text_data_json = json.loads(text_data)

            if text_data_json.get("action") == "load_history":
                before_id = text_data_json.get("before_id")
                messages, has_more = await database_sync_to_async(get_history_page)(
                    self.room_name, before_id=before_id
                )
                await self.send(text_data=json.dumps(
                    {"type": "history", "messages": messages, "has_more": has_more}
                ))
                return

            # Validate presence of message key
            if "message" not in text_data_json:
                raise KeyError('Missing "message" in received data')

            # Rate limiting
            if now - ChatConsumer.user_last_message_time[real_user_key] < RATE_LIMIT_SECONDS:
                logger.warning(f"Rate limit exceeded for {real_user_key}")
                return

            ChatConsumer.user_last_message_time[real_user_key] = now

            # Escape message for XSS prevention
            message = html.escape(text_data_json["message"])

            # Enforce max length
            if len(message) > MAX_MESSAGE_LENGTH:
                message = message[:MAX_MESSAGE_LENGTH]

            # Profanity/harassment moderation -- block, don't persist or
            # broadcast, and don't mask+send (that leaves harassment in the
            # room, just censored).
            if contains_profanity(message):
                await database_sync_to_async(ModerationLog.objects.create)(
                    user=self.scope["user"],
                    room_name=self.room_name,
                    category="profanity",
                )
                await self.send(text_data=json.dumps(
                    {"type": "message_blocked", "reason": "moderation"}
                ))
                return

            current_time = django_timezone.now().astimezone(CHAT_TIMEZONE).strftime("%I:%M:%S %p")
            logger.info(f"Message in {self.room_name} from {real_user_key}")

            await database_sync_to_async(ChatMessage.objects.create)(
                user=self.scope["user"],
                pseudonym=self.pseudonym,
                room_name=self.room_name,
                chat_day=get_chat_day(),
                content=message,
            )

            # Broadcast message to room -- pseudonym only, never the real identity.
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user": self.pseudonym,
                    "time": current_time,
                },
            )

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {real_user_key}")
        except KeyError as e:
            logger.warning(f"Missing key in message from {real_user_key}: {e}")

    async def send_user_list(self):
        user_list = list(ChatConsumer.rooms_users.get(self.room_group_name, {}).values())
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "user_list_update", "users": user_list}
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps({
                "message": event["message"],
                "user": event["user"],
                "time": event["time"]
            })
        )

    async def user_list_update(self, event):
        await self.send(
            text_data=json.dumps({"users": event["users"]})
        )

    async def day_ended(self, event):
        # Triggered by chat.tasks.end_chat_day via group_send at 23:59 Asia/Jerusalem.
        # Silent, no message payload -- the client distinguishes this from any
        # other disconnect purely by the close code.
        await self.close(code=4000)
