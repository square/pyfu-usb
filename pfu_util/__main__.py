"""Command-line interface (CLI) for pfu-util."""

import argparse
import logging
import os
import pkg_resources
import sys

from . import list_devices, DeviceFirmwareUpdater

logger = logging.getLogger(__name__)


def main():
    """CLI entry-point."""
    parser = argparse.ArgumentParser(
        description="Python device firmware update utility."
    )
    parser.add_argument(
        "-D",
        "--download",
        dest="file",
        help="Write firmware from <file> into device",
        required=False,
    )
    parser.add_argument(
        "-a",
        "--address",
        dest="address",
        help="Specify device address in hex for binary download",
        required=False,
    )
    parser.add_argument(
        "-m",
        "--mass-erase",
        dest="erase",
        help="Erase the whole DFU device",
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
        "-d",
        "--device",
        dest="device",
        help="Specify DFU device in hex as <vid>:<pid>",
        required=False,
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
        "-v",
        "--verbose",
        dest="verbose",
        help="Print verbose debug statements",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    # Set log level based on verbosity argument
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, stream=sys.stdout, format="%(message)s"
    )

    # Get pfu-util verion
    if args.version:
        logger.info(pkg_resources.require("pfu_util")[0].version)
        return 0

    # Parse VID/PID if provided
    if args.device:
        vidpid = args.device.split(":")
        if len(vidpid) != 2:
            logger.error("Invalid device argument, see progam help")
            return -1
        else:
            vid, pid = vidpid
            vid, pid = int(vid, 16), int(pid, 16)
            logger.debug("VID = %X, PID = %X", vid, pid)
    else:
        # TODO: If DFU file is provided, should be able to get VID/PID from it
        vid, pid = None, None

    if args.list:
        logger.debug("Listing DFU devices")
        list_devices(vid=vid, pid=pid)
        return 0

    if not args.erase and not args.file:
        logger.error("No action specified, see program help")
        return -1

    dfu_device = DeviceFirmwareUpdater(vid=vid, pid=pid)

    if args.erase:
        dfu_device.mass_erase()

    if args.file:
        address = int(args.address, 16) if args.address else None
        dfu_device.download(args.file, base_address=address)

    return 0
