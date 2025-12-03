import sys
import os

# Add the parent directory to sys.path so we can import main, store, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
