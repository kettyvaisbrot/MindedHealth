def format_food(log):
    return [
        ('Breakfast', 'Yes' if log.breakfast_ate else 'No'),
        ('Lunch', 'Yes' if log.lunch_ate else 'No'),
        ('Dinner', 'Yes' if log.dinner_ate else 'No'),
    ]


def format_sport(log):
    sport_name = log.other_sport if log.sport_type == 'other' else log.get_sport_type_display()
    return [
        ('Did sport', 'Yes' if log.did_sport else 'No'),
        ('Type', sport_name or '—'),
    ]


def format_sleep(log):
    hours = log.get_sleep_hours()
    return [
        ('Went to sleep', str(log.went_to_sleep_yesterday) if log.went_to_sleep_yesterday else '—'),
        ('Woke up', str(log.wake_up_time) if log.wake_up_time else '—'),
        ('Hours slept', f"{hours:.1f}" if hours is not None else '—'),
    ]


def format_meeting(log):
    return [
        ('Type', log.get_meeting_type_display() if log.meeting_type else '—'),
        ('Positivity rating', f"{log.positivity_rating}/5"),
    ]


def format_seizure(log):
    return [
        ('Time', str(log.time) if log.time else '—'),
        ('Duration', f"{log.duration_minutes} minutes"),
    ]


def format_medication(log, medication_names):
    return [
        ('Medication', medication_names.get(log.medication_ref_id, 'Unknown')),
        ('Taken at', str(log.time_taken) if log.time_taken else 'Not taken yet'),
    ]
