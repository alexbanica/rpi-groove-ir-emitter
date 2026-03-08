from abc import ABC, abstractmethod


class GpioConnectionFactoryInterface(ABC):
    @abstractmethod
    def create_connection(self):
        pass
