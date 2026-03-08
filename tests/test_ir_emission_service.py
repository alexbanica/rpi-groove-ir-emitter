import unittest

from ir_emitter.applications.services.IrEmissionService import IrEmissionService
from ir_emitter.domains.dtos.EmitOptionsDto import EmitOptionsDto
from ir_emitter.domains.entities.IrPulseFrame import IrPulseFrame
from ir_emitter.domains.interfaces.PulseEmitterInterface import PulseEmitterInterface
from ir_emitter.domains.interfaces.PulseLoaderInterface import PulseLoaderInterface


class _FakeLoader(PulseLoaderInterface):
    def __init__(self, frame: IrPulseFrame):
        self.frame = frame
        self.loaded_path = None

    def load(self, file_path: str) -> IrPulseFrame:
        self.loaded_path = file_path
        return self.frame


class _FakeEmitter(PulseEmitterInterface):
    def __init__(self):
        self.calls = []

    def play(self, pulses: list[int], repeat: int = 1):
        self.calls.append((pulses, repeat))

    def cleanup(self):
        pass


class IrEmissionServiceTest(unittest.TestCase):
    def test_load_frame_uses_loader(self):
        expected = IrPulseFrame(gpio_in=16, pulse_us=[100, 200])
        loader = _FakeLoader(expected)
        service = IrEmissionService(loader)

        frame = service.load_frame("examples/ventilator-onoff.json")

        self.assertEqual("examples/ventilator-onoff.json", loader.loaded_path)
        self.assertEqual(expected.gpio_in, frame.gpio_in)
        self.assertEqual(expected.pulse_us, frame.pulse_us)

    def test_emit_frame_uses_repeat_from_options(self):
        frame = IrPulseFrame(gpio_in=16, pulse_us=[1, 2, 3, 4])
        loader = _FakeLoader(frame)
        emitter = _FakeEmitter()
        service = IrEmissionService(loader)

        options = EmitOptionsDto(out_gpio=12, carrier_hz=38000, duty_cycle=0.33, repeat=3)
        service.emit_frame(emitter, frame, options)

        self.assertEqual([([1, 2, 3, 4], 3)], emitter.calls)


if __name__ == "__main__":
    unittest.main()
