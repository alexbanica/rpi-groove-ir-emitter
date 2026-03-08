class CliEmitResponse:
    def __init__(self, success: bool, message: str):
        self.success = bool(success)
        self.message = message
