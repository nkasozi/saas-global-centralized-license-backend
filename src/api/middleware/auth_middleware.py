from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.core.ports.auth_interface import AuthInterface
from src.core.ports.logger_interface import LoggerInterface

end_product_user_paths = [
    "/api/v1/users/license/activate",
    "/api/v1/users/license/check-status",
    "/api/v1/users/license/deactivate",
]
brands_url_paths = "/api/v1/brands"


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service: AuthInterface, logger: LoggerInterface):
        super().__init__(app)
        self.auth_service = auth_service
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        if path.startswith(brands_url_paths):
            is_create_brand_request = path == brands_url_paths and method == "POST"

            if not is_create_brand_request:
                api_key = request.headers.get("X-API-KEY")
                if not api_key:
                    self.logger.warning(f"Missing X-API-KEY header for {path}")
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Missing X-API-KEY header"},
                    )

                brand_id_result = self.auth_service.validate_brand_api_key(api_key)
                if brand_id_result.is_err():
                    self.logger.warning(f"Invalid X-API-KEY for {path}")
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid API key"},
                    )

                request.state.brand_id = brand_id_result.unwrap()
                request.state.api_key = api_key

        elif path in end_product_user_paths:
            license_key = request.headers.get("X-LICENSE-KEY")
            if not license_key:
                self.logger.warning(f"Missing X-LICENSE-KEY header for {path}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing X-LICENSE-KEY header"},
                )

            license_key_id_result = self.auth_service.validate_license_key(license_key)
            if license_key_id_result.is_err():
                self.logger.warning(f"Invalid X-LICENSE-KEY for {path}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid license key"},
                )

            request.state.license_key_id = license_key_id_result.unwrap()
            request.state.license_key = license_key

        response = await call_next(request)
        return response
