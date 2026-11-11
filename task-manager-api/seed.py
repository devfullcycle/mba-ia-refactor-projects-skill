"""Atalho de compatibilidade para popular o banco: `python seed.py [--reset]`."""
import sys

from src.app import create_app
from src.config.seed import run_seed

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_seed(reset="--reset" in sys.argv)
