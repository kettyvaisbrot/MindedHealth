import os
import django

# Must be set and django.setup() must be called before any test module is
# imported during collection, because Django model imports trigger the app
# registry check immediately at import time.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MindedHealth.settings")
django.setup()
