class BusinessException(Exception):
    def __init__(self, message, field: str = None):
        super().__init__(message)
        self.field = field
