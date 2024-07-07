from django.db import models
from django.contrib.auth.models import User
from datetime import date

# Create your models here.

class FoodLog(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    breakfast_ate = models.BooleanField(default=False)
    breakfast_time = models.TimeField(null=True, blank=True)
    lunch_ate = models.BooleanField(default=False)
    lunch_time = models.TimeField(null=True, blank=True)
    dinner_ate = models.BooleanField(default=False)
    dinner_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"Food Log on {self.date} for {self.user.username}"

class SportLog(models.Model):
    SPORT_CHOICES = [
        ('swimming', 'Swimming'),
        ('running', 'Running'),
        ('walking', 'Walking'),
        ('gym', 'Gym Session'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    did_sport = models.BooleanField(default=False)
    sport_type = models.CharField(max_length=10, choices=SPORT_CHOICES, null=True, blank=True)
    other_sport = models.CharField(max_length=100, null=True, blank=True)
    sport_time = models.TimeField(default='00:00:00')  # New field for sport time

    def __str__(self):
        if self.sport_time:
            return f"Sport Log on {self.date} at {self.sport_time.strftime('%H:%M')} for {self.user.username}"
        else:
            return f"Sport Log on {self.date} for {self.user.username}"
        
class SleepingLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    sleep_time = models.TimeField()
    wake_time = models.TimeField()
    woke_up_during_night = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s sleep on {self.date}"
        

class Meetings(models.Model):
    MEETING_TYPES_CHOICES = [
        ('family', 'With Family'),
        ('friends', 'With Friends'),
        ('business', 'Business Meeting'),
        ('strangers', 'With Strangers'),

    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    met_people = models.BooleanField(default=False)
    positivity_rating = models.IntegerField(default=1, choices=[(i, str(i)) for i in range(1, 6)])
    meeting_type = models.CharField(max_length=10, choices=MEETING_TYPES_CHOICES, null=True, blank=True)
    

    def __str__(self):
        return f"Meeting on {self.date}"
    
class SeizureLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField()
    last_memory = models.TextField()

    def __str__(self):
            return f"Seizure at {self.date} {self.time}"
    





