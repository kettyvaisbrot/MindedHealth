from rest_framework import serializers
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog


class FoodLogSerializer(serializers.ModelSerializer):
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


class SportLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SportLog
        fields = [
            "date",
            "did_sport",
            "sport_type",
            "other_sport",
            "sport_time",
        ]

    def validate(self, data):
        sport_type = data.get('sport_type')
        other_sport = data.get('other_sport')

        if sport_type == 'other' and not other_sport:
            raise serializers.ValidationError({
                'other_sport': 'Please specify the other sport if sport type is "other".'
            })
        return data


class SleepingLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    went_to_sleep_yesterday = serializers.TimeField(
        required=False, allow_null=True, default=None
    )
    wake_up_time = serializers.TimeField(required=False, allow_null=True, default=None)

    class Meta:
        model = SleepingLog
        fields = [
            "went_to_sleep_yesterday",
            "wake_up_time",
        ]


class MeetingsSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    positivity_rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Meetings
        fields = [
            "date",
            "time",
            "met_people",
            "positivity_rating",
            "meeting_type",
        ]


class SeizureLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SeizureLog
        fields = [
            "date",
            "time",
            "duration_minutes",
        ]
