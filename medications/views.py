# medications/views.py
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from rest_framework import generics
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Medication, MedicationLog
from .serializers import MedicationSerializer, MedicationLogSerializer
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic import UpdateView
from rest_framework import status
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime
from rest_framework.permissions import IsAuthenticated


@method_decorator(login_required, name='dispatch')
class MedicationListView(TemplateView):
    template_name = "medications/medications.html"

@method_decorator(login_required, name='dispatch')
class MedicationListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationSerializer

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(login_required, name='dispatch')
class MedicationDeleteView(generics.DestroyAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

def medications_home(request):

    return reverse_lazy('medications:list')  

@method_decorator(login_required, name='dispatch')
class UpdateMedicationView(UpdateView):
    model = Medication
    fields = ['name', 'daily_dose', 'times_per_day']  
    template_name = 'medications/medication_update.html'  
    success_url = reverse_lazy('dashboard:dashboard_home') 

    def get_object(self, queryset=None):
        return get_object_or_404(Medication, pk=self.kwargs['pk'], user=self.request.user)
    def post(self, request, *args, **kwargs):
        date = request.POST.get('date')
        medications = Medication.objects.filter(user=request.user)

        for medication in medications:
            for i in range(medication.times_per_day):
                taken = request.POST.get(f'medication_{medication.id}_{i}') == 'on'
                time_taken = request.POST.get(f'time_{medication.id}_{i}')

                if taken and time_taken:
                    MedicationLog.objects.update_or_create(
                        medication=medication,
                        date=date,
                        time_taken=time_taken,
                        defaults={'user': request.user}
                    )
        
        return redirect('dashboard:dashboard_home')  


from django.shortcuts import render, redirect
from django.views import View
from .models import Medication, MedicationLog
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import datetime

@method_decorator(login_required, name='dispatch')
class AddMedicationLogView(View):
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')  
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:

            return redirect('dashboard:dashboard_home')

        medications = Medication.objects.filter(user=request.user)
        medication_logs = MedicationLog.objects.filter(user=request.user, date=date)

        context = {
            'current_date': date,
            'medications': medications,
            'medication_logs': medication_logs,
        }
        return render(request, 'medications/add_medication_log.html', context)



    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        date = request.POST.get('date')
        print(f"date_str : {date}")
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:

            return redirect('dashboard:dashboard_home')
        
        medications = Medication.objects.filter(user=request.user)
        for medication in medications:
            for i in range(medication.times_per_day):
                taken = request.POST.get(f'medication_{medication.id}_{i}') == 'on'
                time_taken = request.POST.get(f'time_{medication.id}_{i}')

                if taken and time_taken:
                    data = {
                        'medication': medication.id,
                        'date': date,
                        'time_taken': time_taken,
                        'user': request.user.pk  
                    }
                    serializer = MedicationLogSerializer(data=data)

                    if serializer.is_valid():
                        serializer.save()
                        print("Data saved:", data)  
                        print(f"Seizure Logs")
                    else:
                        print(serializer.errors)
                        print(f"Serialization errors encountered:")
                        return redirect('dashboard:dashboard_home') 

        return HttpResponseRedirect(reverse('dashboard:dashboard_home') + f'?date={date}')


