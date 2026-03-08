from abc import ABC, abstractmethod

from ir_emitter.domains.entities.IrPulseFrame import IrPulseFrame


class PulseLoaderInterface(ABC):
    @abstractmethod
    def load(self, file_path: str) -> IrPulseFrame:
        pass
