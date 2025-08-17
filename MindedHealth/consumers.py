import json
import datetime
import html
import logging
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from collections import defaultdict

logger = logging.getLogger(__name__)

# Optional: simple profanity filter
PROFANITY_LIST = ["badword1", "badword2"]  # extend as needed
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

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.room_group_name not in ChatConsumer.rooms_users:
            ChatConsumer.rooms_users[self.room_group_name] = {}

        ChatConsumer.rooms_users[self.room_group_name][self.channel_name] = self.scope["user"].username
        await self.send_user_list()

    async def disconnect(self, close_code):
        if self.room_group_name in ChatConsumer.rooms_users:
            ChatConsumer.rooms_users[self.room_group_name].pop(self.channel_name, None)

        await self.send_user_list()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        user = self.scope["user"].username
        now = time.time()

        try:
            text_data_json = json.loads(text_data)

            # Validate presence of message key
            if "message" not in text_data_json:
                raise KeyError('Missing "message" in received data')

            # Rate limiting
            if now - ChatConsumer.user_last_message_time[user] < RATE_LIMIT_SECONDS:
                logger.warning(f"Rate limit exceeded for {user}")
                return

            ChatConsumer.user_last_message_time[user] = now

            # Escape message for XSS prevention
            message = html.escape(text_data_json["message"])

            # Enforce max length
            if len(message) > MAX_MESSAGE_LENGTH:
                message = message[:MAX_MESSAGE_LENGTH]

            # Optional profanity filter
            for badword in PROFANITY_LIST:
                message = message.replace(badword, "*" * len(badword))

            current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
            logger.info(f"Message in {self.room_name} from {user}")

            # Broadcast message to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user": user,
                    "time": current_time,
                },
            )

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {user}")
        except KeyError as e:
            logger.warning(f"Missing key in message from {user}: {e}")

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
