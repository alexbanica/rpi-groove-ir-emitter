import json
import os
import tempfile
import unittest

from ir_emitter.infrastructures.persistences.JsonPulseLoader import JsonPulseLoader


class JsonPulseLoaderTest(unittest.TestCase):
    def test_loads_expected_json_shape(self):
        loader = JsonPulseLoader()
        payload = {
            "gpio_in": 16,
            "pulse_us": [9000, 4500, 560],
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as handle:
            json.dump(payload, handle)
            file_path = handle.name

        try:
            frame = loader.load(file_path)
            self.assertEqual(16, frame.gpio_in)
            self.assertEqual([9000, 4500, 560], frame.pulse_us)
        finally:
            os.unlink(file_path)


if __name__ == "__main__":
    unittest.main()
