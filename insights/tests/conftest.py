import os
import sys

# Required by pytest-django when no pytest.ini defines DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MindedHealth.settings")

# Allow full-flow tests to import from insights_service (`from app.xxx import`)
_insights_service_path = os.path.join(os.path.dirname(__file__), "..", "..", "insights_service")
if _insights_service_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_insights_service_path))
