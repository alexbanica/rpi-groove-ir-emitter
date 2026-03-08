from ir_emitter.domains.dtos.EmitOptionsDto import EmitOptionsDto
from ir_emitter.domains.entities.IrPulseFrame import IrPulseFrame
from ir_emitter.domains.interfaces.PulseEmitterInterface import PulseEmitterInterface
from ir_emitter.domains.interfaces.PulseLoaderInterface import PulseLoaderInterface


class IrEmissionService:
    def __init__(self, pulse_loader: PulseLoaderInterface):
        self._pulse_loader = pulse_loader

    def load_frame(self, file_path: str) -> IrPulseFrame:
        return self._pulse_loader.load(file_path)

    def emit_frame(self, emitter: PulseEmitterInterface, frame: IrPulseFrame, options: EmitOptionsDto):
        emitter.play(frame.pulse_us, repeat=options.repeat)
