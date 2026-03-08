import sys
import unittest
from unittest.mock import patch

from ir_emitter.controllers.CliController import CliController


class CliControllerTest(unittest.TestCase):
    def test_parse_args_preserves_defaults(self):
        controller = CliController()

        with patch.object(sys, "argv", ["prog", "examples/ventilator-onoff.json"]):
            request = controller.parse_args()

        self.assertEqual("examples/ventilator-onoff.json", request.file_path)
        self.assertEqual(12, request.out_gpio)
        self.assertEqual(38000, request.carrier_hz)
        self.assertEqual(1, request.repeat)
        self.assertEqual(0.33, request.duty_cycle)


if __name__ == "__main__":
    unittest.main()
