# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Medication, MedicationLog
from django.http import JsonResponse


@login_required
def medication_list(request):
    """Display a list of medications for the logged-in user."""
    medications = Medication.objects.filter(user=request.user)
    return render(request, "medications/medications.html", {"medications": medications})


@login_required
def add_medication(request):
    """Add a new medication."""
    if request.method == "POST":
        name = request.POST.get("name")
        dose = request.POST.get("dose")
        times_per_day = request.POST.get("times_per_day")
        dose_times = request.POST.getlist("dose_times")

        medication = Medication.objects.create(
            name=name,
            dose=dose,
            times_per_day=times_per_day,
            user=request.user,
            dose_times=dose_times,
        )
        return redirect("medications:medication_list")

    return render(request, "medications/add_medication.html")


@login_required
def edit_medication(request, pk):
    """Edit an existing medication."""
    medication = get_object_or_404(Medication, pk=pk, user=request.user)

    if request.method == "POST":
        medication.name = request.POST.get("name")
        medication.dose = request.POST.get("dose")
        medication.times_per_day = request.POST.get("times_per_day")
        medication.dose_times = request.POST.getlist("dose_times")
        medication.save()
        return redirect("medications:medication_list")

    return render(
        request, "medications/edit_medication.html", {"medication": medication}
    )


@login_required
def delete_medication(request, pk):
    """Delete a medication."""
    medication = get_object_or_404(Medication, pk=pk, user=request.user)
    medication.delete()
    return redirect("medications:medication_list")


@login_required
def log_medication(request):
    """Log the medication taken."""
    if request.method == "POST":
        medication_id = request.POST.get("medication_id")
        date = request.POST.get("date")
        time_taken = request.POST.get("time_taken")
        dose_index = request.POST.get("dose_index")

        medication = get_object_or_404(Medication, pk=medication_id, user=request.user)
        MedicationLog.objects.create(
            user=request.user,
            medication=medication,
            date=date,
            time_taken=time_taken,
            dose_index=dose_index,
        )
        return redirect("medications:medication_list")

    return render(request, "medications/log_medication.html")


def keep_alive(request):
    return JsonResponse({"status": "success"})
