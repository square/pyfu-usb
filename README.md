# Python Device Firmware Update Utility

This package is a device firmware update (DFU) utility built on `pyusb`. It aims to provide the same functionality as [`dfu-util`](http://dfu-util.sourceforge.net/), but allow for easy integration into cross-platform Python projects.

## Motivation

`dfu-util` is a very useful tool for performing firmware updates with microcontrollers that support the [DFU USB class](https://www.usb.org/sites/default/files/DFU_1.1.pdf). But for Python projects it is another dependency that must be downloaded in different ways depending on the platform (e.g. macOS, Linux). A native [1] Python implementation would be better for this use case.

The _OpenMV_ project has a tool called [`pydfu`](https://github.com/openmv/openmv/blob/9f06eb4fe15f4f181250aa5848c3e3e51bb85506/tools/pydfu.py) that does this. However, there are some limitations that this package intends to address:

- It is not a standalone Python package, meaning it can't be reused easily in multiple Python projects [2].
- It uses `.dfu` files as input, instead of more common firmware file types like `.bin` and `.hex`.
- It hard codes the device address, since the tool is intended for STM32 microcontrollers only.

In the short-term, we will address these three limitations. In the long-term, it would be great if this package could be CLI-compatible with `dfu-util`.

### Footnotes

1. Even though the package may appear "pure Python", by relying on `pyusb` we rely on `libusb` being installed. See the [`pyusb` docs](https://github.com/pyusb/pyusb#requirements-and-platform-support) for more details on platform support.
2. There is a package on PyPi called [`stm32tool`](https://pypi.org/project/stm32tool/) which bundles the _OpenMV_ `pydfu.py` and a script called `dfu.py` that converts `.bin` and `.hex` files to `.dfu` files. However like _OpenMV_, this package is also STM32 specific.

## Name Choice

Criteria for the package name choice (`pfu-util`) were:

- Be unique from `dfu-util`, in case a user has both installed.
- [`pydfu`](https://pypi.org/project/pydfu/) already taken on PyPi and `py-dfu` would be too similar.
- `py-dfu-util` felt too verbose. 
