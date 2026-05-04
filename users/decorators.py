from functools import wraps
from django.http import HttpResponseForbidden


def therapist_required(view_func):
    """Allow access only to authenticated users whose role is 'therapist'.

    Must be stacked beneath @login_required so that unauthenticated requests
    are redirected to the login page before this check runs:

        @login_required
        @therapist_required
        def my_view(request): ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'therapist':
            return HttpResponseForbidden(
                "Access denied. This feature is only available to therapists."
            )
        return view_func(request, *args, **kwargs)
    return wrapper