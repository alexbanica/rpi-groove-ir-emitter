import time

from ir_emitter.domains.interfaces.PulseEmitterInterface import PulseEmitterInterface


class PigpioPulseEmitter(PulseEmitterInterface):
    def __init__(self, pigpio_connection, gpio_out: int, carrier_hz: int, duty_cycle: float):
        self._pigpio_connection = pigpio_connection
        self._gpio_out = int(gpio_out)
        self._carrier_hz = int(carrier_hz)
        self._duty_cycle = float(duty_cycle)

    def _carrier_wave(self, mark_us: int) -> list:
        pigpio = self._import_pigpio()
        period_us = int(1_000_000 / self._carrier_hz)
        on_us = int(period_us * self._duty_cycle)
        off_us = period_us - on_us

        pulses = []
        cycles = max(1, int(mark_us / period_us))
        for _ in range(cycles):
            if on_us > 0:
                pulses.append(pigpio.pulse(1 << self._gpio_out, 0, on_us))
            if off_us > 0:
                pulses.append(pigpio.pulse(0, 1 << self._gpio_out, off_us))

        rem = mark_us - cycles * period_us
        if rem > 0:
            pulses.append(pigpio.pulse(1 << self._gpio_out, 0, rem))

        return pulses

    def play(self, pulses: list[int], repeat: int = 1):
        pigpio = self._import_pigpio()

        self._pigpio_connection.set_mode(self._gpio_out, pigpio.OUTPUT)
        self._pigpio_connection.write(self._gpio_out, 0)

        wave_pulses = []
        for index, duration in enumerate(pulses):
            if index % 2 == 0:
                wave_pulses.extend(self._carrier_wave(duration))
            else:
                if duration > 0:
                    wave_pulses.append(pigpio.pulse(0, 1 << self._gpio_out, duration))

        self._pigpio_connection.wave_clear()
        self._pigpio_connection.wave_add_generic(wave_pulses)
        wave_id = self._pigpio_connection.wave_create()
        if wave_id < 0:
            raise RuntimeError(f"Failed to create wave: {wave_id}")

        try:
            for _ in range(repeat):
                self._pigpio_connection.wave_send_once(wave_id)
                while self._pigpio_connection.wave_tx_busy():
                    time.sleep(0.001)
        finally:
            self._pigpio_connection.wave_delete(wave_id)

    def cleanup(self):
        try:
            self._pigpio_connection.write(self._gpio_out, 0)
        except Exception:
            pass

    def _import_pigpio(self):
        import pigpio

        return pigpio
