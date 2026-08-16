from chat.moderation import contains_profanity


def test_detects_listed_word(settings):
    settings.CHAT_PROFANITY_WORDS = ["חרא", "מניאק"]
    assert contains_profanity("אתה חרא") is True


def test_detects_listed_word_case_insensitive(settings):
    settings.CHAT_PROFANITY_WORDS = ["shit"]
    assert contains_profanity("you SHIT") is True


def test_word_not_in_list_is_not_flagged(settings):
    settings.CHAT_PROFANITY_WORDS = ["חרא"]
    assert contains_profanity("אתה מניאק") is False


def test_clean_message_not_flagged(settings):
    settings.CHAT_PROFANITY_WORDS = ["חרא", "מניאק"]
    assert contains_profanity("היי, מה שלומך היום?") is False


def test_empty_word_list_never_flags_anything(settings):
    settings.CHAT_PROFANITY_WORDS = []
    assert contains_profanity("אתה חרא ומניאק") is False
