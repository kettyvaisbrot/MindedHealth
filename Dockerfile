# Django Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-django.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader stopwords


COPY . /app

# Build-time only: DJANGO_DEBUG=True avoids the fail-closed ALLOWED_HOSTS check
# in settings.py, which would otherwise abort collectstatic (no real request
# ever reaches this -- DJANGO_DEBUG from docker-compose's .env overrides it
# at runtime).
RUN DJANGO_DEBUG=True python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "MindedHealth.asgi:application"]
