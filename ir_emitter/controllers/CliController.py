import argparse
import sys

from ir_emitter.applications.services.IrEmissionService import IrEmissionService
from ir_emitter.controllers.requests.CliEmitRequest import CliEmitRequest
from ir_emitter.controllers.responses.CliEmitResponse import CliEmitResponse
from ir_emitter.domains.dtos.EmitOptionsDto import EmitOptionsDto
from ir_emitter.infrastructures.emitters.PigpioPulseEmitter import PigpioPulseEmitter
from ir_emitter.infrastructures.gpio.PigpioConnectionFactory import PigpioConnectionFactory
from ir_emitter.infrastructures.persistences.JsonPulseLoader import JsonPulseLoader
from ir_emitter.shared.constants.CliStrings import CliStrings
from ir_emitter.shared.constants.EmitterDefaults import EmitterDefaults


class CliController:
    def __init__(self):
        self._emission_service = IrEmissionService(JsonPulseLoader())

    def parse_args(self) -> CliEmitRequest:
        parser = argparse.ArgumentParser(description=CliStrings.DESCRIPTION)
        parser.add_argument("file", type=str, help=CliStrings.ARG_FILE_HELP)
        parser.add_argument("--out-gpio", type=int, default=EmitterDefaults.OUT_GPIO, help=CliStrings.ARG_OUT_GPIO_HELP)
        parser.add_argument("--carrier", type=int, default=EmitterDefaults.CARRIER_HZ, help=CliStrings.ARG_CARRIER_HELP)
        parser.add_argument("--repeat", type=int, default=EmitterDefaults.REPEAT, help=CliStrings.ARG_REPEAT_HELP)

        args = parser.parse_args()
        return CliEmitRequest(
            file_path=args.file,
            out_gpio=args.out_gpio,
            carrier_hz=args.carrier,
            duty_cycle=EmitterDefaults.DUTY_CYCLE,
            repeat=args.repeat,
        )

    def execute(self, request: CliEmitRequest) -> CliEmitResponse:
        pi_connection = PigpioConnectionFactory().create_connection()
        if not pi_connection.connected:
            print(CliStrings.PIGPIO_CONNECT_ERROR)
            sys.exit(2)

        frame = self._emission_service.load_frame(request.file_path)
        print(CliStrings.LOADED_DURATIONS.format(
            count=len(frame.pulse_us),
            file=request.file_path,
            gpio_in_file=frame.gpio_in,
        ))

        options = EmitOptionsDto(
            out_gpio=request.out_gpio,
            carrier_hz=request.carrier_hz,
            duty_cycle=request.duty_cycle,
            repeat=request.repeat,
        )
        emitter = PigpioPulseEmitter(
            pigpio_connection=pi_connection,
            gpio_out=options.out_gpio,
            carrier_hz=options.carrier_hz,
            duty_cycle=options.duty_cycle,
        )

        try:
            self._emission_service.emit_frame(emitter, frame, options)
            print(CliStrings.PLAYBACK_FINISHED)
        finally:
            emitter.cleanup()
            pi_connection.stop()

        return CliEmitResponse(success=True, message=CliStrings.PLAYBACK_FINISHED)
