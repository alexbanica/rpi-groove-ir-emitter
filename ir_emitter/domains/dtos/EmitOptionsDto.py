class EmitOptionsDto:
    def __init__(self, out_gpio: int, carrier_hz: int, duty_cycle: float, repeat: int):
        self.out_gpio = int(out_gpio)
        self.carrier_hz = int(carrier_hz)
        self.duty_cycle = float(duty_cycle)
        self.repeat = int(repeat)
