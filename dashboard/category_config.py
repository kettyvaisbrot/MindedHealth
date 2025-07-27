from .models import (
    FeltOffLog,
    SleepingLog,
    FoodLog,
    SportLog,
    Meetings,
)
from dashboard.services.questions_service import get_felt_off_questions, get_medication_questions
from medications.models import Medication,MedicationLog


CATEGORY_CONFIG = {
    'felt_off': {
        "display_name": "Moments I Felt Off",
        "model": FeltOffLog,
        "questions": get_felt_off_questions,
        "fields": ["had_moment", "duration", "intensity", "description"],
    },
    'sleep': {
        'model': SleepingLog,
        'fields': ['went_to_sleep_yesterday', 'wake_up_time', 'woke_up_during_night'],
        'questions': [
            {
                'field': 'went_to_sleep_yesterday',
                'question': "🕙 When did you go to sleep?",
                'type': 'time'
            },
            {
                'field': 'wake_up_time',
                'question': "⏰ When did you wake up?",
                'type': 'time'
            },
            {
                'field': 'woke_up_during_night',
                'question': "🌙 Did you wake up during the night?",
                'type': 'select',
                'options': ['yes', 'no']
            }
        ]
    },
    'food': {
    'model': FoodLog,
    'fields': [
        'breakfast_ate', 'breakfast_time',
        'lunch_ate', 'lunch_time',
        'dinner_ate', 'dinner_time'
    ],
    'questions': [
        {
            'field': 'breakfast_ate',
            'question': "🍳 Did you eat breakfast today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'breakfast_time',
            'question': "⏰ What time did you have breakfast?",
            'type': 'time',
            'condition': {
                'field': 'breakfast_ate',
                'value': 'yes'
            }
        },
        {
            'field': 'lunch_ate',
            'question': "🥗 Did you eat lunch today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'lunch_time',
            'question': "⏰ What time did you have lunch?",
            'type': 'time',
            'condition': {
                'field': 'lunch_ate',
                'value': 'yes'
            }
        },
        {
            'field': 'dinner_ate',
            'question': "🍽️ Did you eat dinner today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'dinner_time',
            'question': "⏰ What time did you have dinner?",
            'type': 'time',
            'condition': {
                'field': 'dinner_ate',
                'value': 'yes'
            }
        }
    ]
    },'sport': {
        'model': SportLog,
        'fields': ['did_sport', 'sport_type', 'other_sport', 'sport_time'],
        'questions': [
            {
                'field': 'did_sport',
                'question': "🏃‍♂️ Did you do any sport today?",
                'type': 'select',
                'options': ['yes', 'no']
            },
            {
                'field': 'sport_type',
                'question': "⚽ What type of sport did you do?",
                'type': 'select',
                'options': ['swimming', 'running', 'walking', 'gym', 'other'],
                'condition': {
                    'field': 'did_sport',
                    'value': 'yes'
                }
            },
            {
                'field': 'other_sport',
                'question': "📝 If other, please specify:",
                'type': 'text',
                'condition': {
                    'field': 'sport_type',
                    'value': 'other'
                }
            },
            {
                'field': 'sport_time',
                'question': "⏰ What time did you exercise?",
                'type': 'time',
                'condition': {
                    'field': 'did_sport',
                    'value': 'yes'
                }
            }
        ]
    },
    'meetings': {
    'model': Meetings,
    'fields': ['met_people', 'time', 'meeting_type', 'positivity_rating'],
    'questions': [
        {
            'field': 'met_people',
            'question': "👥 Did you meet anyone today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'time',
            'question': "⏰ What time did you meet them?",
            'type': 'time',
            'condition': {
                'field': 'met_people',
                'value': 'yes'
            }
        },
        {
            'field': 'meeting_type',
            'question': "📌 What kind of meeting was it?",
            'type': 'select',
            'options': ['family', 'friends', 'business', 'strangers'],
            'condition': {
                'field': 'met_people',
                'value': 'yes'
            }
        },
        {
            'field': 'positivity_rating',
            'question': "😊 How positive did the meeting feel? (1 = bad, 5 = great)",
            'type': 'select',
            'options': ['1', '2', '3', '4', '5'],
            'condition': {
                'field': 'met_people',
                'value': 'yes'
            }
        }
    ]
},
    'medication': {
        'model': MedicationLog,
        'fields': [],
        'questions': get_medication_questions,
    },

}
