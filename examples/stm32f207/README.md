# STM32F207 Example

This directory contains an example program to test this package on the
STM32F207. STM32 is a nice hardware platform for testing, since the bootloader
supports DFU over USB and no extra debug hardware is necessary.

The `big_blinky` program toggles GPIOB.7 at a rate of 1 Hz. On the Nucleo-144
board, this is the blue LED labeled `LD2`. The program also includes a large
array of junk data to inflate the binary size, giving better test coverage for
the download sequence.

To enter DFU bootloader, the `BOOT0` pin must be pulled high during reset.
On the Nucleo-144 board specifically, short CN11.7 to one of VDD pins (e.g.
"3V3" on CN8) and then power cycle the board. The device should enumerate over
USB in DFU mode.

A pre-built binary file is committed to the repository, so building is not necessary. However the steps are included below for reference.

## Using

To download this program to an STM32F207 in DFU mode:

```bash
pyfu-usb --download big_blinky.bin --address 8000000 --device 0483:df11
```

## Building

To build the `big_blinky` program, you need Rust installed and a couple of
additional tools. See <https://www.rust-lang.org/tools/install> for Rust
installation instructions.

Add the STM32F207 target:

```bash
rustup target add thumbv7m-none-eabi
```

Install `cargo-binutils`:

```bash
rustup component add llvm-tools-preview
cargo install cargo-binutils
```

Build the program:

```bash
cd big_blinky/
cargo build
cargo objcopy -- -O binary ../big_blinky.bin
```
