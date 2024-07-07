from rest_framework import serializers
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog

class FoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodLog
        fields = '__all__'

class SportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportLog
        fields = '__all__'

class SleepingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepingLog
        fields = '__all__'


class MeetingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meetings
        fields = '__all__'

class SeizureLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeizureLog
        fields = '__all__'


