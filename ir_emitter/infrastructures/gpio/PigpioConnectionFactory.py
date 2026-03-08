from ir_emitter.domains.interfaces.GpioConnectionFactoryInterface import GpioConnectionFactoryInterface
from ir_emitter.shared.constants.CliStrings import CliStrings


class PigpioConnectionFactory(GpioConnectionFactoryInterface):
    def create_connection(self):
        pigpio = self._import_pigpio()
        return pigpio.pi()

    def _import_pigpio(self):
        try:
            import pigpio
        except Exception:
            print(CliStrings.PIGPIO_IMPORT_ERROR_1)
            print(CliStrings.PIGPIO_IMPORT_ERROR_2)
            print(CliStrings.PIGPIO_IMPORT_ERROR_3)
            raise

        return pigpio
