# Copyright 2022 Block, Inc.
"""Command-line interface (CLI) for pyfu-usb."""

import argparse
import logging
import sys

import pkg_resources
import usb
from rich.logging import RichHandler

from . import download, list_devices

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Define command-line arguments for pyfu-usb.

    Returns:
        ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Python device firmware update utility."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        help="Print verbose debug statements",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-V",
        "--version",
        dest="version",
        help="Print the version number",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="list",
        help="List available DFU devices",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-D",
        "--download",
        dest="file",
        help="Download firmware from <file> to device",
        required=False,
    )
    parser.add_argument(
        "-a",
        "--address",
        dest="address",
        help="Specify device address in hex for DfUse devices",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--device",
        dest="device",
        help="Specify DFU device in hex as <vid>:<pid>",
        required=False,
    )
    parser.add_argument(
        "-i",
        "--interface",
        dest="interface",
        help="Specify which USB interface to use for downloading (default: 0)",
        required=False,
        default=0,
    )

    return parser


def cli(args: argparse.Namespace) -> int:
    """Command-line interface (CLI) for pyfu-usb.

    Args:
        args: Command-line arguments.

    Returns:
        0 for success, 1 for failure.
    """
    # Set log level based on verbosity argument
    logging.basicConfig(
        format="%(message)s",
        datefmt="%H:%M:%S.%f",
        level=logging.DEBUG if args.verbose else logging.INFO,
        handlers=[RichHandler()],
    )

    # Get pyfu-usb verion
    if args.version:
        logger.info(pkg_resources.require("pyfu_usb")[0].version)
        return 0

    # Parse VID/PID if provided
    if args.device:
        vidpid = args.device.split(":")
        if len(vidpid) != 2:
            logger.error("Invalid device argument, see progam help")
            return 1

        vid, pid = vidpid
        vid, pid = int(vid, 16), int(pid, 16)
        logger.debug("VID = %X, PID = %X", vid, pid)
    else:
        vid, pid = None, None

    # Parse address if provided
    if args.address:
        address = int(args.address, 16)
    else:
        address = None

    # List DFU devices
    if args.list:
        list_devices(vid=vid, pid=pid)
        return 0

    # Download file to DFU device
    try:
        if args.file:
            download(
                args.file,
                interface=args.interface,
                vid=vid,
                pid=pid,
                address=address,
            )
    except (
        RuntimeError,
        ValueError,
        FileNotFoundError,
        IsADirectoryError,
        usb.core.USBError,
    ) as err:
        logger.error("DFU download failed: %s", repr(err))
        return 1

    return 0


def main() -> None:
    """CLI entry point."""
    sys.exit(cli(create_parser().parse_args()))


if __name__ == "__main__":
    main()
