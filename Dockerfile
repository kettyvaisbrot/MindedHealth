# Use a Python base image
FROM python:3.9-slim

# Set environment variables to avoid Python buffering
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install dependencies for your application (you can adjust as needed)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your application into the container
COPY . /app/

# Expose port 8000 for the Django app
EXPOSE 8000

# Run the application using Gunicorn (change "mindedhealth" to your project folder name)
CMD ["gunicorn", "mindedhealth.wsgi:application", "--bind", "0.0.0.0:8000"]
