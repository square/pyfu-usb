# pyfu-usb: Python USB Firmware Updater

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A small library for firmware updates over USB with devices that support the [DFU](https://www.usb.org/sites/default/files/DFU_1.1.pdf) and [DfuSe](http://dfu-util.sourceforge.net/dfuse.html) protocols. Specifically, `pyfu-usb` supports _listing_ DFU capable devices and _downloading binary files_ to them.

## Compared to [`dfu-util`](http://dfu-util.sourceforge.net/)

`dfu-util` is the popular host side tool for interacting with DFU/DfuSe devices. `pyfu-usb` has only a small sliver the functionality contained in `dfu-util`: Listing and downloading binary files. The reason you would use `pyfu-usb` over `dfu-util` is if you have a Python project that needs firmware update capabilities and don't want an external (non-Python) dependency.

## Compared to [`pydfu.py`](https://github.com/openmv/openmv/blob/9f06eb4fe15f4f181250aa5848c3e3e51bb85506/tools/pydfu.py)

`pydfu.py` is a tool in the _OpenMV_ project that solves the exact problem described above, but it is only for DfuSe devices (e.g. STM32) and also hard codes a number of parameters including device address and max transfer size. It also appears to only work with `.dfu` files, which require an extra conversion step. Since binary files can be directly generated by many embedded toolchains using them is simpler, although less portable.

The code in this package originates from `pydfu.py` and the _OpenMV_ license agreement has been copied into the repository. Along with refactoring the code and adding support for "classic" DFU devices, several modernizations were added:

- Colored logs and progress bar with `rich`
- Using `logging` instead of `print` for output messages
- Consistent style and linting with `ruff`

## Dependencies

Even though this package may appear pure Python, by relying on `pyusb` we rely on `libusb` being installed. See the [`pyusb` docs](https://github.com/pyusb/pyusb#requirements-and-platform-support) for more details on platform support.

## User Guide

Install with `pip`:

    pip install pyfu-usb

List connected DFU devices:

    pyfu-usb --list

Download a file to a DfuSe capable device, specifying a start address in hex:

    pyfu-usb --download <filename> -a <start_address>

Download a file to a DFU capable device:

    pyfu-usb --download <filename>

Use the `--device` argument to specify the `vid:pid` of the device in hex if multiple are connected. See the [examples](examples/) directory for more detailed examples.

## Developer Guide

This project uses [`uv`](https://docs.astral.sh/uv/) for Python tooling. It also uses [`just`](https://github.com/casey/just) to simplify running project specific specific commands.

To install pre-commit hooks (e.g. style, linting):

    just setup

To run pre-commit hooks:

    just lint

To run unit tests:

    just test

To view code coverage:

    just coverage

To build the package:

    uv build

## Contributing

Please see the [documentation](.github/CONTRIBUTING.md) prior to contributing.

## License

Licensed under the [MIT license](LICENSE).
