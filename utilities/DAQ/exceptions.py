class DAQUnknownError(Exception):
    """Custom exception class."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class DAQOpenError(Exception):
    """Custom exception class."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class DAQConnectionError(Exception):
    """Custom exception class."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class DAQResponseError(Exception):
    """Custom exception class."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message