# Examples

This directory contains a [`Makefile`](Makefile) demonstrating how to use
`dfu-util` and `pfu-util` with different hardware.

## STM32

STM32 is the simplest hardware platform to test with since the bootloader
provided by ST supports DFU. The bootloader will support DFU over USB if the
microcontroller itself supports USB.

This example is a blinky program for the Nucleo-144 board and the STM32F207
chip. The program blinks LD2 (blue LED) at 1 Hz.

To enter DFU on any STM32 device, the `BOOT0` pin must be pulled high during
reset. On the Nucleo-144 board specifically, short CN11.7 to one of VDD pins
(e.g. "3V3" on CN8) and then power cycle the board. The device should
enumerate over USB in DFU mode.

The process of entering DFU and the commands in the Makefile should be the same
for any STM32 part, but the prebuilt binary in this directory is just for the
STM32F207 and Nucleo-144.
