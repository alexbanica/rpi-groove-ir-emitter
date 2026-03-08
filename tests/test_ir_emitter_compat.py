import json
import os
import tempfile
import unittest

from ir_emitter.IREmitter import IREmitter


class IREmitterCompatTest(unittest.TestCase):
    def test_load_pulses_keeps_legacy_shape(self):
        payload = {
            "gpio_in": 7,
            "pulse_us": [120, 240, 360],
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as handle:
            json.dump(payload, handle)
            file_path = handle.name

        try:
            gpio_in, pulses = IREmitter.load_pulses(file_path)
            self.assertEqual(7, gpio_in)
            self.assertEqual([120, 240, 360], pulses)
        finally:
            os.unlink(file_path)


if __name__ == "__main__":
    unittest.main()
