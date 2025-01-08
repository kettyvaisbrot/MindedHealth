
# my_statistics/urls.py

from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'my_statistics'

urlpatterns = [
    path('statistics/', views.statistics_view, name='statistics_view'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('keep-alive/', views.keep_alive, name='keep_alive'),


]
