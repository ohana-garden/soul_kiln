"""Entry point for the Virtue Basin Platform."""

from src.cli.commands import cli

__all__ = ["cli"]

if __name__ == "__main__":
    cli()
