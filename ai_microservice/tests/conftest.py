import sys
import os

# Allow `from main import app` / `import internal_jwt` to resolve correctly
# when running pytest from the project root (e.g. `pytest ai_microservice/tests/`)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
