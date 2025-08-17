import re
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit




# Redirect logged-in users from login/register
def redirect_authenticated(user, redirect_to="dashboard:dashboard_home"):
    if user.is_authenticated:
        return redirect(redirect_to)
    return None

@never_cache
def home(request):
    return render(request, "home.html", {"is_authenticated": request.user.is_authenticated})

@require_http_methods(["GET"])
def room(request, room_name):
    # Validate room_name to prevent XSS or injection
    if not re.match(r'^[\w-]+$', room_name):
        return redirect("home")
    return render(request, "chat/room.html", {"room_name": room_name})

@csrf_protect
@never_cache
@ratelimit(key='ip', rate='5/m', method='POST', block=True)  # Max 5 registrations per minute per IP
def register(request):
    # Redirect logged-in users
    redirect_resp = redirect_authenticated(request.user)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard:dashboard_home")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})

@csrf_protect
@never_cache
@ratelimit(key='ip', rate='5/m', method='POST', block=True)  # Max 5 login attempts per minute per IP
def login_view(request):
    redirect_resp = redirect_authenticated(request.user, redirect_to="home")
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

@require_http_methods(["POST"])
@csrf_protect
def custom_logout_view(request):
    logout(request)
    return redirect("home")

@require_http_methods(["GET"])
@ratelimit(key='ip', rate='30/m', method='GET', block=True)  # Prevent abuse
def keep_alive(request):
    return JsonResponse({"status": "success"})
