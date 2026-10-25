import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from domain.exceptions.business_exception import BusinessException
from domain.exceptions.not_found_exception import NotFoundException
from web.commons.api_response import ApiResponse

logger = logging.getLogger(__name__)

_HTTP_EXCEPTION_CODES = {
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
}


def register_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        code = _HTTP_EXCEPTION_CODES.get(exc.status_code, "HTTP_ERROR")
        response = ApiResponse.failure(error=str(exc.detail), code=code)

        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(mode="json"),
            headers=exc.headers,
        )

    @app.exception_handler(BusinessException)
    async def business_exception_handler(
        request: Request, exc: BusinessException
    ) -> JSONResponse:
        response = ApiResponse.failure(error=str(exc), code="BUSINESS_ERROR")
        if exc.field:
            response.data = {exc.field: str(exc)}

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(
        request: Request, exc: NotFoundException
    ) -> JSONResponse:
        response = ApiResponse.failure(error=str(exc), code="NOT_FOUND")

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors[field] = error["msg"]

        response = ApiResponse.failure(
            error="Validation failed", code="VALIDATION_ERROR"
        )

        response.data = errors

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        response = ApiResponse.failure(error=str(exc), code="INVALID_VALUE")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Erro não tratado em %s %s", request.method, request.url.path
        )

        error_message = str(exc) if app.debug else "An unexpected error occurred"

        response = ApiResponse.failure(error=error_message, code="INTERNAL_ERROR")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(mode="json"),
        )
