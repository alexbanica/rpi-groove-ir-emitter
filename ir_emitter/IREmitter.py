#!/usr/bin/env python3
# language: python

import json
import time
from typing import List
from ir_emitter import DEFAULT_CARRIER_HZ, DEFAULT_DUTY_CYCLE

try:
    import pigpio
except Exception as e:
    print("Error importing pigpio. Make sure 'pigpio' Python package is installed.")
    print("Install: pip3 install pigpio")
    print("Also start the daemon: sudo pigpiod")
    raise


class IREmitter:
    def __init__(self, pi: pigpio.pi, gpio_out: int, carrier_hz: int = DEFAULT_CARRIER_HZ, duty_cycle: float = DEFAULT_DUTY_CYCLE):
        self.pi = pi
        self.gpio = gpio_out
        self.carrier_hz = int(carrier_hz)
        self.duty_cycle = float(duty_cycle)
        self._carrier_on_wave_id = None

    def _carrier_wave(self, mark_us: int):
        # pigpio waveforms are defined using pigpio.pulse objects with gpio_on, gpio_off, delay (us)
        # To create a carrier we toggle the GPIO on/off for each carrier cycle.
        # Carrier period (microseconds)
        period_us = int(1_000_000 / self.carrier_hz)
        on_us = int(period_us * self.duty_cycle)
        off_us = period_us - on_us
        pulses = []
        cycles = max(1, int(mark_us / period_us))
        for _ in range(cycles):
            if on_us > 0:
                pulses.append(pigpio.pulse(1 << self.gpio, 0, on_us))
            if off_us > 0:
                pulses.append(pigpio.pulse(0, 1 << self.gpio, off_us))
        # adjust last pulse duration to account for remainder
        rem = mark_us - cycles * period_us
        if rem > 0:
            # add a final on or off depending on remainder; simplest: add one last on pulse with rem length
            pulses.append(pigpio.pulse(1 << self.gpio, 0, rem))
        return pulses

    def play(self, pulses: List[int], repeat: int = 1):
        pi = self.pi
        gpio = self.gpio

        pi.set_mode(gpio, pigpio.OUTPUT)
        pi.write(gpio, 0)

        # Build waveform once for the entire sequence
        # pigpio uses pulses referencing GPIO masks; to avoid conflicts we construct pulses for the pin.
        wave_pulses = []
        for i, dur in enumerate(pulses):
            if i % 2 == 0:
                # mark -> carrier ON bursts for 'dur' microseconds
                wave_pulses.extend(self._carrier_wave(dur))
            else:
                # space -> ensure line off for dur microseconds
                if dur > 0:
                    wave_pulses.append(pigpio.pulse(0, 1 << gpio, dur))
        # Clear existing waves and create new one
        pi.wave_clear()
        pi.wave_add_generic(wave_pulses)
        wid = pi.wave_create()
        if wid < 0:
            raise RuntimeError(f"Failed to create wave: {wid}")
        try:
            for _ in range(repeat):
                pi.wave_send_once(wid)
                # wait until done
                while pi.wave_tx_busy():
                    time.sleep(0.001)
                    # If caller interrupts, break
        finally:
            pi.wave_delete(wid)

    def cleanup(self):
        try:
            self.pi.write(self.gpio, 0)
        except Exception:
            pass

    @staticmethod
    def load_pulses(filename: str) -> (int, List[int]):
        with open(filename, "r") as f:
            data = json.load(f)
        return int(data.get("gpio_in", -1)), [int(x) for x in data["pulse_us"]]
