import datetime

import pytest
from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from chat.models import ChatMessage, PseudonymAssignment
from chat.services import get_chat_day
from chat.tasks import end_chat_day
from MindedHealth.consumers import ChatConsumer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass12345", role="patient")


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    # end_chat_day() always notifies the channel layer, even in tests that only
    # care about the DB cleanup -- avoid needing a real local Redis for any of them.
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


@pytest.mark.django_db
def test_end_chat_day_deletes_todays_messages_and_pseudonyms(user):
    chat_day = get_chat_day()

    ChatMessage.objects.create(
        user=user, pseudonym="Calm Fox 42", room_name="patient",
        chat_day=chat_day, content="today's message",
    )
    PseudonymAssignment.objects.create(
        user=user, room_name="patient", chat_day=chat_day, pseudonym="Calm Fox 42",
    )

    end_chat_day()

    assert ChatMessage.objects.filter(room_name="patient", chat_day=chat_day).count() == 0
    assert PseudonymAssignment.objects.filter(room_name="patient", chat_day=chat_day).count() == 0


@pytest.mark.django_db
def test_end_chat_day_does_not_touch_a_different_day(user):
    other_day = datetime.date(2020, 1, 1)

    ChatMessage.objects.create(
        user=user, pseudonym="Calm Fox 42", room_name="patient",
        chat_day=other_day, content="old message from another day",
    )
    PseudonymAssignment.objects.create(
        user=user, room_name="patient", chat_day=other_day, pseudonym="Calm Fox 42",
    )

    end_chat_day()

    assert ChatMessage.objects.filter(chat_day=other_day).count() == 1
    assert PseudonymAssignment.objects.filter(chat_day=other_day).count() == 1


@pytest.mark.django_db
def test_end_chat_day_cleans_both_rooms(user):
    chat_day = get_chat_day()

    for room in ("patient", "family"):
        ChatMessage.objects.create(
            user=user, pseudonym="X", room_name=room, chat_day=chat_day, content="msg",
        )

    end_chat_day()

    assert ChatMessage.objects.filter(chat_day=chat_day).count() == 0


@pytest.mark.django_db(transaction=True)
def test_end_chat_day_disconnects_connected_clients_with_code_4000(user):
    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()  # your_pseudonym
        await communicator.receive_json_from()  # initial history page
        await communicator.receive_json_from()  # initial user_list_update

        await sync_to_async(end_chat_day, thread_sensitive=False)()

        closed = await communicator.receive_output()
        assert closed["type"] == "websocket.close"
        assert closed.get("code") == 4000

        await communicator.disconnect()

    async_to_sync(scenario)()
