FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
    && apt-get install -y gcc libpq-dev libmariadb-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*



WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install gunicorn
# Pre-download NLTK data to avoid downloading on runtime
RUN python -m nltk.downloader punkt wordnet stopwords omw-1.4

COPY . /app/

EXPOSE 8000


CMD ["gunicorn", "MindedHealth.wsgi:application", "--bind", "0.0.0.0:8000"]
