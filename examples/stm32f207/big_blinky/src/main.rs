//! Blinky program for the STM32F207. Toggles GPIOB.7 at 1 Hz. Has a large,
//! useless string to make the program binary larger for testing DFU.

#![no_std]
#![no_main]

use cortex_m::peripheral::syst::SystClkSource;
use cortex_m_rt::entry;
use stm32f2::stm32f217;
extern crate panic_halt;

static BLOAT_BINARY: &str = include_str!("random-text.txt");

#[entry]
fn main() -> ! {
    let _dont_optimize = &BLOAT_BINARY[100..200];

    // Get peripherals
    let cm_periph = cortex_m::Peripherals::take().unwrap();
    let pac_periph = stm32f217::Peripherals::take().unwrap();

    // Configure SysTick to one second (16 MHz HSI is default clock)
    let mut systick = cm_periph.SYST;
    systick.set_clock_source(SystClkSource::Core);
    systick.set_reload(16_000_000);
    systick.enable_counter();

    // Enable LED (GPIO B.7 on Nucleo-144): Enable clock, set pin output mode
    let rcc = pac_periph.RCC;
    rcc.ahb1enr.write(|w| w.gpioben().set_bit());

    let gpiob = pac_periph.GPIOB;
    gpiob.moder.write(|w| w.moder7().bits(0b01));

    loop {
        // Toggle LED
        if gpiob.odr.read().odr7().is_low() {
            gpiob.odr.write(|w| w.odr7().set_bit());
        } else {
            gpiob.odr.write(|w| w.odr7().clear_bit());
        }

        // Delay for 1 second
        while !systick.has_wrapped() {}
    }
}
