#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import sys
from ir_emitter.IREmitter import IREmitter
from ir_emitter import DEFAULT_CARRIER_HZ

try:
    import pigpio
except Exception as e:
    print("Error importing pigpio. Make sure 'pigpio' Python package is installed.")
    print("Install: pip3 install pigpio")
    print("Also start the daemon: sudo pigpiod")
    raise

def main():
    parser = argparse.ArgumentParser(description="Record IR signals (raw pulses).")
    parser.add_argument("file", type=str, help="JSON file with recorded pulses")
    parser.add_argument("--out-gpio", type=int, default=12, help="GPIO pin number for IR transmitter (BCM)")
    parser.add_argument("--carrier", type=int, default=DEFAULT_CARRIER_HZ, help="Carrier frequency in Hz (e.g. 38000)")
    parser.add_argument("--repeat", type=int, default=1, help="How many times to repeat the frame")

    args = parser.parse_args()

    pi = pigpio.pi()
    if not pi.connected:
        print("Could not connect to pigpio daemon. Start it with: sudo pigpiod")
        sys.exit(2)

    gpio_in_file, pulses = IREmitter.load_pulses(args.file)
    print(f"Loaded {len(pulses)} durations from {args.file} (recorded input GPIO: {gpio_in_file})")
    player = IREmitter(pi, args.out_gpio, carrier_hz=args.carrier)
    try:
        player.play(pulses, repeat=args.repeat)
        print("Playback finished.")
    finally:
        player.cleanup()
        pi.stop()


if __name__ == "__main__":
    main()