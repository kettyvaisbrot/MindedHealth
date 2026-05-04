import sys
import os

# Allow `from app.xxx import` to resolve correctly when running pytest
# from the project root (e.g. `pytest insights_service/tests/`)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
