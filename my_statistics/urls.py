
# my_statistics/urls.py

from django.urls import path
from . import views

app_name = 'my_statistics'

urlpatterns = [
    path('statistics/', views.statistics_view, name='statistics_view'),
    # Add more URLs for other statistics categories as needed
]
