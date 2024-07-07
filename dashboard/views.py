from rest_framework.renderers import JSONRenderer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
import datetime
from medications.models import Medication, MedicationLog
import json
import requests
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
from .serializers import (
    FoodLogSerializer, SportLogSerializer, SleepingLogSerializer, 
    MeetingsSerializer, SeizureLogSerializer
)
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse
from django.views.generic import View
from rest_framework.decorators import api_view
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone





def dashboard_home(request):
    date = request.GET.get('date')
    context = {}
    # Get the choices for meeting_type from the Meetings model
    meeting_type_choices = Meetings.MEETING_TYPES_CHOICES
    if date:
        context['date'] = date
        context['today'] = timezone.now().date().strftime('%Y-%m-%d')
        food_logs = FoodLog.objects.filter(user=request.user, date=date)
        sport_logs = SportLog.objects.filter(user=request.user, date=date)
        sleeping_logs = SleepingLog.objects.filter(user=request.user, date=date)
        meetings_logs = Meetings.objects.filter(user=request.user, date=date)
        meeting_type_choices = Meetings.MEETING_TYPES_CHOICES
        seizure_logs = SeizureLog.objects.filter(user=request.user, date=date)
        medications = Medication.objects.filter(user=request.user)
        if medications.exists():
            times_per_day_range = range(max(medications.values_list('times_per_day', flat=True)))
        else:
            times_per_day_range = [0]
        medication_logs = MedicationLog.objects.filter(user=request.user, date=date)

        # Prepare data to checkboxes and time inputs
        medication_log_data = {}
        for log in medication_logs:
            if log.medication.id not in medication_log_data:
                medication_log_data[log.medication.id] = []
            medication_log_data[log.medication.id].append(log.time_taken)
        context['food_logs'] = food_logs
        context['sport_logs'] = sport_logs
        context['sleeping_logs'] = sleeping_logs
        context['meetings_logs'] = meetings_logs
        context['is_current_date'] = (date == context['today'])
        context['meeting_type_choices'] = meeting_type_choices
        context['seizure_logs'] = seizure_logs
        context['sport_choices'] = SportLog.SPORT_CHOICES
        context['medications'] = medications
        context['medication_logs'] = medication_logs
        context['medication_log_data'] = medication_log_data
        context['times_per_day_range'] = times_per_day_range
        context['seizure_logs'] = seizure_logs
    return render(request, 'dashboard/dashboard.html', context)



class FoodLogAPIView(APIView):
    def get(self, request, date):
        food_logs = FoodLog.objects.filter(user=request.user, date=date)
        serializer = FoodLogSerializer(food_logs, many=True)
        if food_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No food log for this date'}, status=status.HTTP_404_NOT_FOUND)


    permission_classes = [IsAuthenticated]

    def post(self, request):
        date = request.data.get('date')
        serializer = FoodLogSerializer(data=request.data)
        if serializer.is_valid():
            FoodLog.objects.update_or_create(
                user=request.user,
                date=date,
                defaults=serializer.validated_data
            )
            return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, date):
        food_log = FoodLog.objects.filter(user=request.user, date=date).first()
        if not food_log:
            return Response({'message': 'Food log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FoodLogSerializer(food_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, date):
        food_log = FoodLog.objects.filter(user=request.user, date=date).first()
        if not food_log:
            return Response({'message': 'Food log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        food_log.delete()
        return Response({'message': 'Food log deleted successfully'})





class SportLogAPIView(APIView):
    def get(self, request, date):
        sport_logs = SportLog.objects.filter(user=request.user, date=date)
        serializer = SportLogSerializer(sport_logs, many=True)
        if sport_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No Sport log for this date'}, status=status.HTTP_404_NOT_FOUND)

    permission_classes = [IsAuthenticated]

    def post(self, request, date=None):
        # Use request.POST to handle form data
        date = request.POST.get('date')
        serializer = SportLogSerializer(data=request.POST)
        if serializer.is_valid():
            # Save or update the SportLog instance
            SportLog.objects.update_or_create(
                user=request.user,
                date=date,
                defaults=serializer.validated_data
            )
            # Redirect to the dashboard with the date parameter
            return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, date):
        sport_log = SportLog.objects.filter(user=request.user, date=date).first()
        if not sport_log:
            return Response({'message': 'Sport log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SportLogSerializer(sport_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, date):
        sport_log = SportLog.objects.filter(user=request.user, date=date).first()
        if not sport_log:
            return Response({'message': 'Sport log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        sport_log.delete()
        return Response({'message': 'Sport log deleted successfully'})




class SleepingLogAPIView(APIView):
    def get(self, request, date):
        sleeping_logs = SleepingLog.objects.filter(user=request.user, date=date)
        serializer = SleepingLogSerializer(sleeping_logs, many=True)
        if sleeping_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No sleeping log for this date'}, status=status.HTTP_404_NOT_FOUND)

    permission_classes = [IsAuthenticated]

    def post(self, request, date=None):
        # Use request.POST to handle form data
        date = request.POST.get('date')
        serializer = SleepingLogSerializer(data=request.POST)
        if serializer.is_valid():
            # Save or update the SportLog instance
            SleepingLog.objects.update_or_create(
                user=request.user,
                date=date,
                defaults=serializer.validated_data
            )
            # Redirect to the dashboard with the date parameter
            return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, date):
        sleeping_log = SleepingLog.objects.filter(user=request.user, date=date).first()
        if not sleeping_log:
            return Response({'message': 'Sleeping log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SleepingLogSerializer(sleeping_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, date):
        sleeping_log = SleepingLog.objects.filter(user=request.user, date=date).first()
        if not sleeping_log:
            return Response({'message': 'Sleeping log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        sleeping_log.delete()
        return Response({'message': 'Sleeping log deleted successfully'})


class MeetingsAPIView(View):
    def get(self, request, date):
        Meetings_logs = Meetings.objects.filter(user=request.user, date=date)
        serializer = MeetingsSerializer(Meetings_logs, many=True)
        if Meetings_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No meetings log for this date'}, status=status.HTTP_404_NOT_FOUND)

    permission_classes = [IsAuthenticated]

    def post(self, request, date=None):
        # Use request.POST to handle form data
        date = request.POST.get('date')
        serializer = MeetingsSerializer(data=request.POST)
        if serializer.is_valid():
            # Save or update the SportLog instance
            Meetings.objects.update_or_create(
                user=request.user,
                date=date,
                defaults=serializer.validated_data
            )
            # Redirect to the dashboard with the date parameter
            return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        data = json.loads(request.body)
        meeting = Meetings.objects.get(pk=pk)
        serializer = MeetingsSerializer(meeting, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'message': 'Meeting updated successfully'})
        return JsonResponse(serializer.errors, status=400)

    def delete(self, request, pk):
        meeting = Meetings.objects.get(pk=pk)
        meeting.delete()
        return JsonResponse({'message': 'Meeting deleted successfully'})


class SeizureLogAPIView(APIView):

    def get(self, request, date):
        sezuirs_logs = SeizureLog.objects.filter(user=request.user, date=date)
        serializer = SeizureLogSerializer(sezuirs_logs, many=True)
        if sezuirs_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No sezuirs_logs for this date'}, status=status.HTTP_404_NOT_FOUND)


    permission_classes = [IsAuthenticated]

    def post(self, request):
        date = request.data.get('date')
        serializer = SeizureLogSerializer(data=request.data)
        if serializer.is_valid():
            SeizureLog.objects.update_or_create(
                user=request.user,
                date=date,
                defaults=serializer.validated_data
            )
            return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        seizure_log = SeizureLog.objects.get(pk=pk)
        serializer = SeizureLogSerializer(seizure_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        seizure_log = SeizureLog.objects.get(pk=pk)
        seizure_log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DailyDocumentationView(View):
    def get(self, request, date=None):
        current_date = datetime.date.today()
        date = date or current_date.strftime('%Y-%m-%d')
        documentation_data = {}

        if date != current_date.strftime('%Y-%m-%d'):
            # Fetch daily documentation data based on the provided date
            api_url = f'http://localhost:8000/daily-documentation/{date}/'
            response = requests.get(api_url)

            if response.status_code == 200:
                documentation_data = response.json()

        context = {
            'date': date,
            'editable': date == current_date.strftime('%Y-%m-%d'),
            'documentation_data': documentation_data,
        }

        return render(request, 'dashboard/dashboard.html', context)