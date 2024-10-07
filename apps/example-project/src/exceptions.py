# Example of how easy it is to create exceptions that can take in any custom data you want


class ApiRequestException(Exception):
    def __init__(self, message, extra: dict):
        self.message = message
        self.extra = extra
        super().__init__(message)
