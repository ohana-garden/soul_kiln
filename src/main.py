"""Entry point for the Virtue Basin Platform."""
import sys
import os

# Add project root to path for imports when running as script
_src_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_src_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.cli.commands import cli

if __name__ == "__main__":
    cli()
