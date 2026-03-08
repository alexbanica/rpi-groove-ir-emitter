#!/usr/bin/env python3

from ir_emitter.controllers.CliController import CliController


def main() -> None:
    controller = CliController()
    request = controller.parse_args()
    controller.execute(request)


if __name__ == "__main__":
    main()
