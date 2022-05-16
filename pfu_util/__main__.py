"""Command-line interface (CLI) for pfu-util."""

from . import dfu_download


def main():
    """CLI entry-point."""
    dfu_download()
