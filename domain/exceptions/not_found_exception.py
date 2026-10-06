from domain.exceptions.business_exception import BusinessException


class NotFoundException(BusinessException):
    """Recurso inexistente. Subclasse de BusinessException; mapeada para 404."""
