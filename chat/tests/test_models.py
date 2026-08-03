import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from chat.models import ChatMessage

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass12345")


@pytest.mark.django_db
def test_message_content_round_trips_through_the_orm(user):
    msg = ChatMessage.objects.create(
        user=user,
        pseudonym="Calm Fox 42",
        room_name="patient",
        chat_day=datetime.date(2026, 1, 1),
        content="hello, this is a real message",
    )

    reloaded = ChatMessage.objects.get(pk=msg.pk)
    assert reloaded.content == "hello, this is a real message"


@pytest.mark.django_db
def test_message_content_is_actually_encrypted_in_the_database(user):
    plaintext = "this must never appear in plaintext in the database"
    msg = ChatMessage.objects.create(
        user=user,
        pseudonym="Calm Fox 42",
        room_name="patient",
        chat_day=datetime.date(2026, 1, 1),
        content=plaintext,
    )

    # Bypass the ORM's decryption entirely and read the raw column value.
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT content FROM {ChatMessage._meta.db_table} WHERE id = %s",
            [msg.pk],
        )
        raw_value = cursor.fetchone()[0]

    assert plaintext not in raw_value
    assert raw_value != plaintext


@pytest.mark.django_db
def test_deleting_user_sets_null_and_keeps_the_message(user):
    msg = ChatMessage.objects.create(
        user=user,
        pseudonym="Calm Fox 42",
        room_name="patient",
        chat_day=datetime.date(2026, 1, 1),
        content="still here after the user is gone",
    )

    user.delete()

    reloaded = ChatMessage.objects.get(pk=msg.pk)
    assert reloaded.user is None
    assert reloaded.content == "still here after the user is gone"


@pytest.mark.django_db
def test_missing_encryption_key_raises_a_clear_error(user, settings):
    settings.CHAT_MESSAGE_ENCRYPTION_KEY = ""

    with pytest.raises(ImproperlyConfigured):
        ChatMessage.objects.create(
            user=user,
            pseudonym="Calm Fox 42",
            room_name="patient",
            chat_day=datetime.date(2026, 1, 1),
            content="should never be saved",
        )
