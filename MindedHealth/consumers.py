import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    # Dictionary to keep track of connected users
    connected_users = {}

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        # Broadcast the user list
        await self.send_user_list()

    async def disconnect(self, close_code):
        # Remove the user from the connected users when they disconnect
        if self.channel_name in self.connected_users:
            del self.connected_users[self.channel_name]

        # Broadcast the updated user list
        await self.send_user_list()

        # Leave the room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)

            # Check if the expected keys are present
            if "message" not in text_data_json:
                raise KeyError('Missing "message" in the received data')

            message = text_data_json["message"]
            user = text_data_json.get("user", None)

            # Log the received message and user for debugging
            print(f"Received message: {message}, User: {user}")

            # Update connected users with the pseudonym if it's their first message
            if user and self.channel_name not in self.connected_users:
                self.connected_users[self.channel_name] = user
            current_time = datetime.datetime.now().strftime("%I:%M:%S %p")

            # Send the message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user": user,
                    "time": current_time,
                },
            )

            # Broadcast the updated user list after each message
            await self.send_user_list()

        except json.JSONDecodeError:
            print("Error: Received message is not valid JSON.")
        except KeyError as e:
            print(f"Error: Missing key in the received message: {e}")

    async def send_user_list(self):
        # Get all connected users' names
        user_list = list(self.connected_users.values())

        # Send the updated user list to all clients in the room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "user_list_update", "users": user_list}
        )

    async def chat_message(self, event):
        message = event["message"]
        user = event["user"]
        time = event["time"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"message": message, "user": user, "time": time})
        )

    async def user_list_update(self, event):
        users = event["users"]

        # Send updated user list to WebSocket
        await self.send(text_data=json.dumps({"users": users}))
