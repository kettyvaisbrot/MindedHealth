from rest_framework import serializers
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog


class FoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodLog
        fields = "__all__"


class SportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportLog
        fields = "__all__"
    def validate(self, data):
        sport_type = data.get('sport_type')
        other_sport = data.get('other_sport')

        if sport_type == 'other' and not other_sport:
            raise serializers.ValidationError({
                'other_sport': 'Please specify the other sport if sport type is "other".'
            })
        return data


class SleepingLogSerializer(serializers.ModelSerializer):
    went_to_sleep_yesterday = serializers.TimeField(
        required=False, allow_null=True, default=None
    )
    wake_up_time = serializers.TimeField(required=False, allow_null=True, default=None)

    class Meta:
        model = SleepingLog
        fields = ["went_to_sleep_yesterday", "wake_up_time"]


class MeetingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meetings
        fields = "__all__"


from .models import SeizureLog


class SeizureLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SeizureLog
        fields = ["user", "date", "time", "duration_minutes"]
