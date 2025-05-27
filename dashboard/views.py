from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
import datetime
import json
import requests
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
from .serializers import (
    FoodLogSerializer, SportLogSerializer, SleepingLogSerializer, 
    MeetingsSerializer, SeizureLogSerializer
)
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.db import models
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from medications.models import MedicationLog, Medication
from medications.serializers import MedicationLogSerializer
from django.views.generic import View

def dashboard_home(request):
    # Get date from request, or set it to empty if not provided
    date_str = request.GET.get('date', '')
    today = timezone.now().date().strftime('%Y-%m-%d')    

    
    # Check if date is provided and valid
    if not date_str:
        messages.warning(request, "Date is required before displaying data.")
        return render(request, 'dashboard/dashboard.html')  # Redirect to the same page

    # Validate date format
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.warning(request, "Invalid date format. Please use YYYY-MM-DD.")
        return render(request, 'dashboard/dashboard.html')

    # If date is valid, proceed to query logs   
    context = {}
    food_logs = FoodLog.objects.filter(user=request.user, date=date)
    sport_logs = SportLog.objects.filter(user=request.user, date=date)
    sleeping_logs = SleepingLog.objects.filter(user=request.user, date=date)
    meetings_logs = Meetings.objects.filter(user=request.user, date=date)
    seizure_logs = SeizureLog.objects.filter(user=request.user, date=date)
    medication_logs = MedicationLog.objects.filter(user=request.user, date=date).select_related('medication')
 
    # Populate context with data
    context['date'] = date
    context['today'] = today
    context['food_logs'] = food_logs
    context['sport_logs'] = sport_logs
    context['sleeping_logs'] = sleeping_logs
    context['meetings_logs'] = meetings_logs
    context['seizure_logs'] = seizure_logs
    context['is_current_date'] = (date == timezone.now().date())
    context['medication_logs'] = medication_logs
    context['sport_choices'] = SportLog.SPORT_CHOICES
    context['meeting_type_choices'] = Meetings.MEETING_TYPES_CHOICES
    return render(request, 'dashboard/dashboard.html', context)


class MedicationLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all medications for the logged-in user
        date = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))  # Default to today
        medications = Medication.objects.filter(user=request.user)
        medication_logs = MedicationLog.objects.filter(user=request.user, date=date)

        context = {
            'medications': medications,
            'medication_logs': medication_logs,  # Include medication logs for the specified date
            'today': timezone.now().date(),
            'selected_date': date,
        }
        return render(request, 'dashboard/log_medication.html', context)

    def post(self, request):
        date = request.data.get('date', timezone.now().date().strftime('%Y-%m-%d'))  # Default to today
        
        # Create a mutable copy of the request data
        data = request.data.copy()
        data['user'] = request.user.id  # Set the user field to the logged-in user's ID

        serializer = MedicationLogSerializer(data=data)
        if serializer.is_valid():
            # Assuming you also have a dose_index in the request data
            MedicationLog.objects.update_or_create(
                user=request.user,
                date=date,
                dose_index=serializer.validated_data['dose_index'],
                defaults={
                    'time_taken': serializer.validated_data['time_taken'],
                    'medication': serializer.validated_data['medication']
                }
            )
            return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# views.py
from django.http import JsonResponse

def keep_alive(request):
    # Simply return a success response to reset the session timer
    return JsonResponse({'status': 'success'})


class FoodLogAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve food logs for a specific date.",
        responses={200: FoodLogSerializer(many=True), 404: "No food log for this date"}
    )
    def get(self, request, date):
        print(request.data)  # Debug: Check what data is coming in
        food_logs = FoodLog.objects.filter(user=request.user, date=date)
        serializer = FoodLogSerializer(food_logs, many=True)
        if food_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No food log for this date'}, status=status.HTTP_404_NOT_FOUND)


    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create or update a food log for a specific date.",
        request_body=FoodLogSerializer,
        responses={302: "Redirects to dashboard after successful save", 400: "Validation errors"}
    )
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
    
    @swagger_auto_schema(
        operation_description="Update an existing food log for a specific date.",
        request_body=FoodLogSerializer,
        responses={200: FoodLogSerializer, 404: "Food log not found for this date", 400: "Validation errors"}
    )
    def put(self, request, date):
        food_log = FoodLog.objects.filter(user=request.user, date=date).first()
        if not food_log:
            return Response({'message': 'Food log not found for this date'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FoodLogSerializer(food_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Delete a food log for a specific date.",
        responses={200: "Food log deleted successfully", 404: "Food log not found for this date"}
    )
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
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        sleeping_logs = SleepingLog.objects.filter(user=request.user, date=date)
        serializer = SleepingLogSerializer(sleeping_logs, many=True)
        if sleeping_logs.exists():
            return Response(serializer.data)
        else:
            return Response({'message': 'No sleeping log for this date'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, date=None):
        # Use request.data to handle JSON data
        date = request.data.get('date')  # Retrieve date from request data
        serializer = SleepingLogSerializer(data=request.data)
        if serializer.is_valid():
            # Save or update the SleepingLog instance
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



class MeetingsAPIView(APIView):
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
    

@login_required
def log_medication(request, date):
    if request.method == 'POST':
        try:
            # Retrieve the time_taken from the form
            time_taken_str = request.POST.get('time_taken')
            medication_id = request.POST.get('medication')

            # Check if time_taken and medication_id exist in the form data
            if not time_taken_str or not medication_id:
                raise ValueError("Time and Medication selection are required.")

            # Convert time_taken from string to a time object
            time_taken = timezone.datetime.strptime(time_taken_str, "%H:%M").time()

            # Get the medication object
            medication = get_object_or_404(Medication, id=medication_id, user=request.user)

            # Retrieve logs for this medication and date
            existing_logs = MedicationLog.objects.filter(
                user=request.user,
                medication=medication,
                date=date
            )
            print(f"Existing logs count: {existing_logs.count()}")

            # Calculate the max dose index, explicitly checking for None
            max_dose_index = existing_logs.aggregate(max_index=models.Max('dose_index'))['max_index']
            if max_dose_index is None:
                max_dose_index = -1
            print(f"Max dose index before saving: {max_dose_index}")

            next_dose_index = max_dose_index + 1
            print(f"Next dose index to be used: {next_dose_index}")

            # Log the new medication entry
            MedicationLog.objects.create(
                user=request.user,
                medication=medication,
                date=date,
                time_taken=time_taken,
                dose_index=next_dose_index
            )
            print(f"Logging medication at time {time_taken} with dose_index {next_dose_index}")

            # Pass a success message to indicate that the entry was saved
            success_message = "Medication entry saved successfully!"

        except Exception as e:
            # Handle any errors and provide feedback
            print(f"An error occurred: {e}")
            return render(request, 'dashboard/dashboard.html', {
                'error_message': f"An error occurred: {e}",
                'date': date
            })

    # Retrieve all logs for the current date to show on the dashboard
    logs_for_date = MedicationLog.objects.filter(user=request.user, date=date)
    
    # Render the same page with the current date data and success message if available
    return render(request, 'dashboard/dashboard.html', {
        'date': date,
        'logs': logs_for_date,
        'success_message': success_message if 'success_message' in locals() else None
    })



