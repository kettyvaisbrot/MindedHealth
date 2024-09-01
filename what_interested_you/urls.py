from django.urls import path
from .views import search_view

app_name = 'what_interested_you'  # Define namespace for the app


urlpatterns = [
    path('search/', search_view, name='search'),  # Ensure this line is present
]
