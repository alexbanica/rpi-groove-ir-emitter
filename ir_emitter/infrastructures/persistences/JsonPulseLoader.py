import json

from ir_emitter.domains.entities.IrPulseFrame import IrPulseFrame
from ir_emitter.domains.interfaces.PulseLoaderInterface import PulseLoaderInterface
from ir_emitter.shared.constants.JsonKeys import JsonKeys


class JsonPulseLoader(PulseLoaderInterface):
    def load(self, file_path: str) -> IrPulseFrame:
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        gpio_in = int(data.get(JsonKeys.GPIO_IN, -1))
        pulses = [int(value) for value in data[JsonKeys.PULSE_US]]
        return IrPulseFrame(gpio_in=gpio_in, pulse_us=pulses)
