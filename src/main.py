"""Entry point for the Virtue Basin Platform."""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.commands import cli

if __name__ == "__main__":
    cli()
