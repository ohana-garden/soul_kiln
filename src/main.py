"""Entry point for the Virtue Basin Platform."""
import sys
import os

# Add parent directory to path so 'src' is importable as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.commands import cli

if __name__ == "__main__":
    cli()
