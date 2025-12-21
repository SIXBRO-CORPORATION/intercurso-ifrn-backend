class JWTError(Exception):
    def __init__(self, message: str = "Erro no processamento do token JWT"):
        self.message = message
        super().__init__(self.message)


class JWTDecodeError(JWTError):
    def __init__(self, message: str = "Não foi possível decodificar o token"):
        super().__init__(message)


class JWTExpiredError(JWTError):
    def __init__(self, message: str = "Token expirado"):
        super().__init__(message)


class JWTValidationError(JWTError):
    def __init__(self, message: str = "Falha na validação do token"):
        super().__init__(message)


class JWTMissingClaimError(JWTError):
    def __init__(self, claim: str):
        message = f"Claim obrigatório ausente: {claim}"
        super().__init__(message)
        self.claim = claim
