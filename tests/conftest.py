# conftest.py
import sys
from pathlib import Path

# Add the src directory to PYTHONPATH
sys.path.append(str(Path(__file__).parents[1] / "src"))
