import pytest
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from datetime import timedelta

from django.utils import timezone

from chat.models import ModerationLog, MuteBan
from MindedHealth.consumers import ChatConsumer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass12345", role="patient")


@pytest.fixture
def family_user(db):
    return User.objects.create_user(username="bob", password="pass12345", role="family")


@pytest.fixture
def therapist_user(db):
    return User.objects.create_user(username="dr_carol", password="pass12345", role="therapist")


@pytest.mark.django_db(transaction=True)
def test_consumer_never_sends_the_real_username_over_the_wire(user, settings):
    """End-to-end: connect, send a message, inspect exactly what goes over the WebSocket wire."""
    # Real channel layer needs a running Redis; tests use the in-memory layer instead,
    # same as Channels' own docs recommend for consumer tests.
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected

        greeting = await communicator.receive_json_from()
        assert greeting["type"] == "your_pseudonym"
        my_pseudonym = greeting["pseudonym"]
        assert my_pseudonym != user.username
        assert user.username not in my_pseudonym

        history = await communicator.receive_json_from()
        assert history["type"] == "history"
        assert history["messages"] == []
        assert history["has_more"] is False

        await communicator.receive_json_from()  # the initial user_list_update

        await communicator.send_json_to({"message": "hello from a real user"})
        broadcast = await communicator.receive_json_from()

        assert broadcast["message"] == "hello from a real user"
        assert broadcast["user"] == my_pseudonym
        assert broadcast["user"] != user.username
        assert user.username not in broadcast["user"]

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_profane_message_is_blocked_not_broadcast_and_logged(db, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    settings.CHAT_PROFANITY_WORDS = ["חרא"]
    # Dedicated username: ChatConsumer.user_last_message_time is a class-level
    # dict shared across tests, so reusing "alice" here can spuriously trip
    # the 1-msg/sec rate limit if another test just sent a message for her.
    moderation_user = User.objects.create_user(
        username="moderation_test_user", password="pass12345", role="patient"
    )

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = moderation_user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()  # your_pseudonym
        await communicator.receive_json_from()  # history
        await communicator.receive_json_from()  # user_list_update

        await communicator.send_json_to({"message": "אתה חרא"})
        response = await communicator.receive_json_from()

        assert response == {"type": "message_blocked", "reason": "moderation"}
        assert await communicator.receive_nothing() is True

        log_count = await database_sync_to_async(ModerationLog.objects.count)()
        assert log_count == 1

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_clean_message_still_broadcasts_normally(db, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    settings.CHAT_PROFANITY_WORDS = ["חרא"]
    clean_user = User.objects.create_user(
        username="clean_message_test_user", password="pass12345", role="patient"
    )

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = clean_user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()  # your_pseudonym
        await communicator.receive_json_from()  # history
        await communicator.receive_json_from()  # user_list_update

        await communicator.send_json_to({"message": "hello, how are you?"})
        broadcast = await communicator.receive_json_from()

        assert broadcast["message"] == "hello, how are you?"

        log_count = await database_sync_to_async(ModerationLog.objects.count)()
        assert log_count == 0

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_message_with_pii_is_blocked_not_broadcast_and_logged(db, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    pii_test_user = User.objects.create_user(
        username="pii_test_user", password="pass12345", role="patient"
    )

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = pii_test_user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()  # your_pseudonym
        await communicator.receive_json_from()  # history
        await communicator.receive_json_from()  # user_list_update

        await communicator.send_json_to({"message": "אפשר לכתוב לי למייל dana.cohen@example.com"})
        response = await communicator.receive_json_from()

        assert response == {"type": "message_blocked", "reason": "pii"}
        assert await communicator.receive_nothing() is True

        log = await database_sync_to_async(ModerationLog.objects.get)()
        assert log.category == "pii"

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_third_violation_closes_socket_with_4002_and_sends_muted(db, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    settings.CHAT_PROFANITY_WORDS = ["חרא"]
    muted_test_user = User.objects.create_user(
        username="third_violation_test_user", password="pass12345", role="patient"
    )

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = muted_test_user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()  # your_pseudonym
        await communicator.receive_json_from()  # history
        await communicator.receive_json_from()  # user_list_update

        # Send 3 profane messages. Reset the rate-limit clock between sends
        # (it's a class-level dict keyed by username, unrelated to what
        # we're testing here -- otherwise these would collide as "too fast").
        for i in range(2):
            ChatConsumer.user_last_message_time[muted_test_user.username] = 0
            await communicator.send_json_to({"message": "אתה חרא"})
            response = await communicator.receive_json_from()
            assert response == {"type": "message_blocked", "reason": "moderation"}

        ChatConsumer.user_last_message_time[muted_test_user.username] = 0
        await communicator.send_json_to({"message": "אתה חרא"})
        muted_response = await communicator.receive_json_from()
        assert muted_response["type"] == "muted"
        assert "muted_until" in muted_response

        closed = await communicator.receive_output()
        assert closed["type"] == "websocket.close"
        assert closed.get("code") == 4002

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_already_muted_user_is_rejected_on_connect(db, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    muted_user = User.objects.create_user(
        username="already_muted_test_user", password="pass12345", role="patient"
    )
    MuteBan.objects.create(user=muted_user, muted_until=timezone.now() + timedelta(hours=1))

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = muted_user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert connected  # accept() is called so the "muted" message can be sent

        muted_response = await communicator.receive_json_from()
        assert muted_response["type"] == "muted"
        assert "muted_until" in muted_response

        closed = await communicator.receive_output()
        assert closed["type"] == "websocket.close"
        assert closed.get("code") == 4002

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_unauthenticated_connection_is_rejected(db):
    from django.contrib.auth.models import AnonymousUser

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = AnonymousUser()
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert not connected

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_family_user_cannot_connect_to_the_patient_room(family_user, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/patient/")
        communicator.scope["user"] = family_user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "patient"}}

        connected, _ = await communicator.connect()
        assert not connected

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_patient_user_cannot_connect_to_the_family_room(user, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

    async def scenario():
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/family/")
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"room_name": "family"}}

        connected, _ = await communicator.connect()
        assert not connected

        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_therapist_cannot_connect_to_either_room(therapist_user, settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

    async def scenario():
        for room_name in ("patient", "family"):
            communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{room_name}/")
            communicator.scope["user"] = therapist_user
            communicator.scope["url_route"] = {"kwargs": {"room_name": room_name}}

            connected, _ = await communicator.connect()
            assert not connected

            await communicator.disconnect()

    async_to_sync(scenario)()
