"""Command-line interface (CLI) for pfu-util."""

import sys

from . import dfu_download


def main():
    """CLI entry-point."""
    dfu_download()


if __name__ == "__main__":
    sys.exit(main())
