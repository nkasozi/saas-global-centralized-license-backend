import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from src.api.http.v1 import brand_routes, end_product_user_routes
from src.api.middleware.auth_middleware import AuthMiddleware
from src.config import settings
from src.infrastructure.auth.auth_service import AuthService
from src.infrastructure.logging.logger_adapter import LoggerAdapter
from src.infrastructure.persistence.file_based_db.brand_repository import BrandRepository
from src.infrastructure.persistence.file_based_db.license_key_repository import LicenseKeyRepository


class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    error_type: str


class ValidationErrorResponse(BaseModel):
    error: str
    status_code: int
    errors: list[ValidationErrorDetail]


def create_application() -> FastAPI:
    app = FastAPI(title=settings.application_name, version=settings.api_version, debug=settings.debug)

    logger = LoggerAdapter()
    brand_repository = BrandRepository()
    license_key_repository = LicenseKeyRepository()
    auth_service = AuthService(brand_repository, license_key_repository, logger)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        formatted_errors = []

        for error in exc.errors():
            field_name = ".".join(str(loc) for loc in error.get("loc", []))
            if field_name.startswith("body."):
                field_name = field_name[5:]

            formatted_errors.append(
                {
                    "field": field_name or "request",
                    "message": error.get("msg", "Validation error"),
                    "error_type": error.get("type", "unknown"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Validation Error", "status_code": 422, "errors": formatted_errors},
        )

    def build_validation_error_response() -> dict:
        return {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "Validation Error"},
                            "status_code": {"type": "integer", "example": 422},
                            "errors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field": {"type": "string", "example": "brand_name"},
                                        "message": {"type": "string", "example": "Field is required"},
                                        "error_type": {"type": "string", "example": "value_error.missing"},
                                    },
                                },
                            },
                        },
                    }
                }
            },
        }

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=settings.application_name,
            version=settings.api_version,
            routes=app.routes,
        )

        validation_error_response = build_validation_error_response()

        for path in openapi_schema.get("paths", {}).values():
            for method in path.values():
                if isinstance(method, dict) and "responses" in method:
                    method["responses"]["422"] = validation_error_response

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    app.add_middleware(AuthMiddleware, auth_service=auth_service, logger=logger)

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    app.include_router(
        brand_routes.router, prefix=f"{settings.api_prefix}/{settings.api_version}/brands", tags=["brands"]
    )

    app.include_router(
        end_product_user_routes.router, prefix=f"{settings.api_prefix}/{settings.api_version}/users", tags=["licenses"]
    )

    @app.get(f"{settings.api_prefix}/health")
    async def health_check() -> dict:
        return {"status": "healthy", "application": settings.application_name}

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.server_port, log_level=settings.log_level.lower())
