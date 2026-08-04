# Django Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-django.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader stopwords


COPY . /app

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "MindedHealth.asgi:application"]
