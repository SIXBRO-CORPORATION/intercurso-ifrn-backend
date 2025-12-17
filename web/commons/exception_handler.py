from dataclasses import field

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from domain.exceptions.business_exception import BusinessException
from web.commons.ApiResponse import ApiResponse


def register_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_exception_handler(
            request: Request,
            exc: BusinessException
    ) -> JSONResponse:
        response = ApiResponse.failure(
            error=str(exc),
            code="BUSINESS_ERROR"
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
            request: Request,
            exc: RequestValidationError
    ) -> JSONResponse:
        errors = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors[field] = error["msg"]

        response = ApiResponse.failure(
            error="Validation failed",
            code="VALIDATION_ERROR"
        )

        response.data = errors

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump()
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
            request: Request,
            exc: ValueError
    ) -> JSONResponse:
        response = ApiResponse.failure(
            error=str(exc),
            code="INVALID_VALUE"
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
            request: Request,
            exc: Exception
    ) -> JSONResponse:
        error_message = (
            str(exc) if app.debug
            else "An unexpected error occurred"
        )

        response = ApiResponse.failure(
            error=error_message,
            code="INTERNAL_ERROR"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump()
        )
