import re
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import get_user_model
from users.forms import CustomUserCreationForm, CustomAuthenticationForm
from users.models import PatientProfile, TherapistProfile, FamilyMemberProfile
from django.contrib.auth.decorators import login_required
User = get_user_model()


def redirect_authenticated(user, redirect_to="dashboard:dashboard_home"):
    if user.is_authenticated:
        return redirect(redirect_to)
    return None

@login_required
def therapist_page(request):
    return render(request, "users/therapist_dashboard.html")

@login_required
def family_member_page(request):
    return render(request, "family_member_page.html")

@never_cache
def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'therapist':
            return render(request, "users/therapist_dashboard.html", {"is_authenticated": True})
        elif request.user.role == 'family':
            return render(request, "family_member_page.html", {"is_authenticated": True})
        else:
            return render(request, "home.html", {"is_authenticated": True})
    return render(request, "home.html", {"is_authenticated": False})

def about(request):
    return render(request, 'about.html')

def features(request):
    return render(request, 'features.html')

@require_http_methods(["GET"])
def room(request, room_name):
    if not re.match(r'^[\w-]+$', room_name):
        return redirect("home")
    return render(request, "chat/room.html", {"room_name": room_name})


@csrf_protect
@never_cache
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    redirect_resp = redirect_authenticated(request.user)
    if redirect_resp:
        return redirect(redirect_resp)

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        role = request.POST.get("role")

        # Check if email already exists
        email = request.POST.get("email")
        if User.objects.filter(email=email).exists():
            form.add_error("email", "This email is already used. Please log in or use another email.")
            return render(request, "register.html", {"form": form})

        if form.is_valid() and role in ["patient", "therapist", "family"]:
            user = form.save(commit=False)
            user.role = role
            user.save()

            if role == "patient":
                PatientProfile.objects.create(user=user)
            elif role == "therapist":
                TherapistProfile.objects.create(user=user)
            elif role == "family":
                patient_email = request.POST.get("patient_email")
                try:
                    patient_user = User.objects.get(email=patient_email, role="patient")
                    FamilyMemberProfile.objects.create(user=user, related_patient=patient_user.patientprofile)
                except User.DoesNotExist:
                    form.add_error("patient_email", "Patient with this email does not exist.")
                    return render(request, "register.html", {"form": form})

            login(request, user)

            if user.role == "patient":
                return redirect("home")
            elif user.role == "therapist":
                return redirect("therapist_dashboard")
            elif user.role == "family":
                return redirect("family_member_page")

    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})



@csrf_protect
@never_cache
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    redirect_resp = redirect_authenticated(request.user)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == "patient":
                return redirect("home")
            elif user.role == "therapist":
                return redirect("therapist_dashboard")
            elif user.role == "family":
                return redirect("family_member_page")
    else:
        form = CustomAuthenticationForm()

    return render(request, "login.html", {"form": form})


@require_http_methods(["POST"])
@csrf_protect
def custom_logout_view(request):
    logout(request)
    return redirect("home")

@require_http_methods(["GET"])
@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def keep_alive(request):
    return JsonResponse({"status": "success"})
