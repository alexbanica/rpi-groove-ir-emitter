from ir_emitter.infrastructures.emitters.PigpioPulseEmitter import PigpioPulseEmitter
from ir_emitter.infrastructures.persistences.JsonPulseLoader import JsonPulseLoader


class IREmitter:
    def __init__(self, pi, gpio_out: int, carrier_hz: int, duty_cycle: float):
        self._emitter = PigpioPulseEmitter(
            pigpio_connection=pi,
            gpio_out=gpio_out,
            carrier_hz=carrier_hz,
            duty_cycle=duty_cycle,
        )

    def play(self, pulses: list[int], repeat: int = 1):
        self._emitter.play(pulses=pulses, repeat=repeat)

    def cleanup(self):
        self._emitter.cleanup()

    @staticmethod
    def load_pulses(filename: str) -> tuple[int, list[int]]:
        frame = JsonPulseLoader().load(filename)
        return frame.gpio_in, frame.pulse_us
