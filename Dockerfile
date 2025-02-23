
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables to prevent Python from writing pyc files
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
    && apt-get install -y gcc libpq-dev libmariadb-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*



# Create and set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your application into the container
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Set the command to run your app using the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
