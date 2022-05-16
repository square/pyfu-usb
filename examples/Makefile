STM32_EXAMPLE_BIN = stm32f207_nucleo144_blinky.bin

.PHONY: stm32_example_dfu_util
stm32_example_dfu_util:
	dfu-util -v \
		-D $(STM32_EXAMPLE_BIN) \
		-d 0483:df11 \
		-a "@Internal Flash  /0x08000000/04*016Kg,01*064Kg,07*128Kg" \
		--dfuse-address 0x8000000:leave
