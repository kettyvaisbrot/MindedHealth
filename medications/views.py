from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Medication
from .services import (
    create_medication,
    update_medication,
    delete_medication,
    log_medication,
)


@login_required
def medication_list(request):
    """Display a list of medications for the logged-in user."""
    medications = Medication.objects.filter(user=request.user)
    return render(request, "medications/medications.html", {"medications": medications})


@login_required
def add_medication(request):
    """Add a new medication."""
    if request.method == "POST":
        create_medication(
            user=request.user,
            name=request.POST.get("name"),
            dose=request.POST.get("dose"),
            times_per_day=request.POST.get("times_per_day"),
            dose_times=request.POST.getlist("dose_times"),
        )
        return redirect("medications:medication_list")

    return render(request, "medications/add_medication.html")


@login_required
def edit_medication(request, pk):
    """Edit an existing medication."""
    medication = get_object_or_404(Medication, pk=pk, user=request.user)

    if request.method == "POST":
        update_medication(
            medication=medication,
            name=request.POST.get("name"),
            dose=request.POST.get("dose"),
            times_per_day=request.POST.get("times_per_day"),
            dose_times=request.POST.getlist("dose_times"),
        )
        return redirect("medications:medication_list")

    return render(
        request, "medications/edit_medication.html", {"medication": medication}
    )


@login_required
def delete_medication(request, pk):
    """Delete a medication."""
    medication = get_object_or_404(Medication, pk=pk, user=request.user)
    delete_medication(medication)
    return redirect("medications:medication_list")


@login_required
def log_medication(request):
    """Log the medication taken."""
    if request.method == "POST":
        medication = get_object_or_404(Medication, pk=request.POST.get("medication_id"), user=request.user)
        log_medication(
            user=request.user,
            medication=medication,
            date=request.POST.get("date"),
            time_taken=request.POST.get("time_taken"),
            dose_index=request.POST.get("dose_index"),
        )
        return redirect("medications:medication_list")

    return render(request, "medications/log_medication.html")


def keep_alive(request):
    return JsonResponse({"status": "success"})
