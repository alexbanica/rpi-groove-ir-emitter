from abc import ABC, abstractmethod


class PulseEmitterInterface(ABC):
    @abstractmethod
    def play(self, pulses: list[int], repeat: int = 1):
        pass

    @abstractmethod
    def cleanup(self):
        pass
