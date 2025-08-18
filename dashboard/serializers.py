from rest_framework import serializers
from django.utils.html import strip_tags
from django.utils.timezone import now as tz_now
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog, FeltOffLog


# --- Helpers / mixins ---

def _sanitize_text(value: str, max_len: int | None = None) -> str:
    """Remove HTML tags, trim whitespace, enforce optional max length."""
    if value is None:
        return value
    cleaned = strip_tags(value).strip()
    if max_len is not None:
        cleaned = cleaned[:max_len]
    return cleaned


class DateNotInFutureMixin:
    """Ensures dates are not in the future."""
    def validate_date(self, value):
        if value and value > tz_now().date():
            raise serializers.ValidationError("Future dates are not allowed.")
        return value



# --- Serializers ---

class FoodLogSerializer(DateNotInFutureMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FoodLog
        fields = [
            "date",
            "breakfast_ate",
            "breakfast_time",
            "lunch_ate",
            "lunch_time",
            "dinner_ate",
            "dinner_time",
        ]

    def validate(self, data):
        """
        If a meal wasn't eaten, null-out its time (prevents stale values and user confusion).
        """
        b_ate = data.get("breakfast_ate")
        l_ate = data.get("lunch_ate")
        d_ate = data.get("dinner_ate")

        if b_ate is False:
            data["breakfast_time"] = None
        if l_ate is False:
            data["lunch_time"] = None
        if d_ate is False:
            data["dinner_time"] = None
        return data


class SportLogSerializer(DateNotInFutureMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    # Defensive length limits for text fields (helps avoid oversized payloads / DoS)
    sport_type = serializers.CharField(required=False, allow_blank=True, max_length=50)
    other_sport = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = SportLog
        fields = [
            "date",
            "did_sport",
            "sport_type",
            "other_sport",
            "sport_time",
        ]

    def validate_other_sport(self, value):
        # Sanitize free text
        if value:
            return _sanitize_text(value, max_len=100)
        return value

    def validate_sport_type(self, value):
        if value:
            return _sanitize_text(value, max_len=50)
        return value

    def validate(self, data):
        did = data.get("did_sport")
        sport_type = data.get("sport_type")
        other_sport = data.get("other_sport")
        sport_time = data.get("sport_time")

        # If sport_type is "other", other_sport becomes required
        if (sport_type or "").lower() == "other" and not other_sport:
            raise serializers.ValidationError({
                "other_sport": 'Please specify the other sport if sport type is "other".'
            })

        # If user did NOT do sport, clear dependent fields
        if did is False:
            data["sport_type"] = None
            data["other_sport"] = None
            data["sport_time"] = None

        # If user did sport, make sure sport_time is non-negative and reasonable
        if did:
            if sport_time is not None:
                try:
                    # sport_time is often an IntegerField; still enforce bounds defensively
                    if int(sport_time) < 0 or int(sport_time) > 1440:
                        raise serializers.ValidationError({"sport_time": "Sport time must be between 0 and 1440 minutes."})
                except (TypeError, ValueError):
                    raise serializers.ValidationError({"sport_time": "Sport time must be an integer number of minutes."})

        return data


class SleepingLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    went_to_sleep_yesterday = serializers.TimeField(required=False, allow_null=True, default=None)
    wake_up_time = serializers.TimeField(required=False, allow_null=True, default=None)

    class Meta:
        model = SleepingLog
        fields = [
            "went_to_sleep_yesterday",
            "wake_up_time",
        ]

    # Cross-field logic could be added if you later store sleep dates explicitly.


class MeetingsSerializer(DateNotInFutureMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    positivity_rating = serializers.IntegerField(min_value=1, max_value=5)
    meeting_type = serializers.CharField(required=False, allow_blank=True, max_length=50)
    met_people = serializers.CharField(required=False, allow_blank=True, max_length=200)

    class Meta:
        model = Meetings
        fields = [
            "date",
            "time",
            "met_people",
            "positivity_rating",
            "meeting_type",
        ]

    def validate_meeting_type(self, value):
        return _sanitize_text(value, max_len=50) if value else value

    def validate_met_people(self, value):
        return _sanitize_text(value, max_len=200) if value else value


class SeizureLogSerializer(DateNotInFutureMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SeizureLog
        fields = [
            "date",
            "time",
            "duration_minutes",
        ]

    def validate_duration_minutes(self, value):
        if value is None:
            return value
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Duration must be an integer number of minutes.")
        if ivalue < 0 or ivalue > 1440:
            raise serializers.ValidationError("Duration must be between 0 and 1440 minutes.")
        return ivalue

class FeltOffLogSerializer(DateNotInFutureMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    description = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )

    class Meta:
        model = FeltOffLog
        fields = [
            "date",
            "had_moment",
            "duration",
            "intensity",
            "description",
        ]

    def validate_duration(self, value):
        return _sanitize_text(value, max_len=100) if value else value

    def validate_description(self, value):
        return _sanitize_text(value, max_len=1000) if value else value
