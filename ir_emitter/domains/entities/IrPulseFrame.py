class IrPulseFrame:
    def __init__(self, gpio_in: int, pulse_us: list[int]):
        self.gpio_in = int(gpio_in)
        self.pulse_us = [int(value) for value in pulse_us]
