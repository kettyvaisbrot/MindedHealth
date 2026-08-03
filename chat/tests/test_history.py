import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from chat.models import ChatMessage
from chat.services import get_chat_day
from MindedHealth.consumers import ChatConsumer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass12345", role="patient")


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


async def _connect_and_drain_greeting(user, room_name="patient"):
    """Connects, consumes your_pseudonym + history + user_list_update, returns the communicator and history payload."""
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{room_name}/")
    communicator.scope["user"] = user
    communicator.scope["url_route"] = {"kwargs": {"room_name": room_name}}

    connected, _ = await communicator.connect()
    assert connected

    await communicator.receive_json_from()  # your_pseudonym
    history = await communicator.receive_json_from()  # history
    await communicator.receive_json_from()  # user_list_update

    return communicator, history


@pytest.mark.django_db(transaction=True)
def test_sending_a_message_persists_it(user):
    async def scenario():
        communicator, _ = await _connect_and_drain_greeting(user)

        await communicator.send_json_to({"message": "this should be saved"})
        await communicator.receive_json_from()  # the live broadcast

        await communicator.disconnect()

    async_to_sync(scenario)()

    saved = ChatMessage.objects.get(room_name="patient")
    assert saved.content == "this should be saved"
    assert saved.chat_day == get_chat_day()


@pytest.mark.django_db(transaction=True)
def test_a_later_connection_sees_earlier_messages_as_history(user):
    ChatMessage.objects.create(
        user=user, pseudonym="Calm Fox 42", room_name="patient",
        chat_day=get_chat_day(), content="sent before this connection existed",
    )

    async def scenario():
        communicator, history = await _connect_and_drain_greeting(user)
        await communicator.disconnect()
        return history

    history = async_to_sync(scenario)()

    assert history["type"] == "history"
    assert len(history["messages"]) == 1
    assert history["messages"][0]["message"] == "sent before this connection existed"
    assert history["has_more"] is False


@pytest.mark.django_db(transaction=True)
def test_history_pagination_returns_newest_page_first_oldest_to_newest_within_it(user):
    chat_day = get_chat_day()
    for i in range(15):
        ChatMessage.objects.create(
            user=user, pseudonym="Calm Fox 42", room_name="patient",
            chat_day=chat_day, content=f"message {i}",
        )

    async def scenario():
        communicator, first_page = await _connect_and_drain_greeting(user)

        await communicator.send_json_to({
            "action": "load_history",
            "before_id": first_page["messages"][0]["id"],
        })
        second_page = await communicator.receive_json_from()

        await communicator.disconnect()
        return first_page, second_page

    first_page, second_page = async_to_sync(scenario)()

    # Newest 10 (messages 5..14) on the first page, oldest-to-newest within it.
    assert [m["message"] for m in first_page["messages"]] == [f"message {i}" for i in range(5, 15)]
    assert first_page["has_more"] is True

    # Remaining 5 (messages 0..4) on the second page, no overlap, no gaps.
    assert [m["message"] for m in second_page["messages"]] == [f"message {i}" for i in range(0, 5)]
    assert second_page["has_more"] is False
