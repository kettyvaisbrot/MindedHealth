from django.urls import path
from .views import search_view

app_name = 'what_interested_you' 


urlpatterns = [
    path('search/', search_view, name='search'), 
]
