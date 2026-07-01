import os

# Required by pytest-django when no pytest.ini defines DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MindedHealth.settings")
