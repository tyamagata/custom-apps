class MalformedCsvException(Exception):
    def __init__(self, message, extra: dict):
        self.message = message
        self.extra = extra
        super().__init__(message, extra)
