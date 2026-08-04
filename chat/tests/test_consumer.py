import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

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
