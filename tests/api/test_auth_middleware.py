from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.api.middleware.auth_middleware import AuthMiddleware
from src.core.models.brand import Brand
from src.core.models.licence_key import LicenseKey
from src.infrastructure.auth.auth_service import AuthService
from src.infrastructure.logging.logger_adapter import LoggerAdapter

TEST_API_KEY = "test-brand-api-key-1234567890123456"
TEST_INVALID_API_KEY = "invalid-api-key"
TEST_LICENSE_KEY = "test-license-key-1234567890123456"
TEST_INVALID_LICENSE_KEY = "invalid-license-key"


@pytest.fixture
def auth_service() -> AuthService:
    logger = LoggerAdapter()
    brand_repository = Mock()
    license_key_repository = Mock()

    brand_id = str(uuid4())
    license_key_id = str(uuid4())

    test_brand = Brand(id=brand_id, brand_name="Test Brand", api_hash_key=TEST_API_KEY)
    test_license_key = LicenseKey(
        id=license_key_id,
        brand_id=brand_id,
        end_product_user_id=str(uuid4()),
        key_string=TEST_LICENSE_KEY,
        license_ids=[],
    )

    brand_repository.get_by_id.return_value.is_err.return_value = False
    brand_repository.get_by_id.return_value.ok_value = test_brand
    brand_repository.save.return_value.is_err.return_value = False
    brand_repository.save.return_value.ok_value = test_brand
    brand_repository.get_all.return_value.is_err.return_value = False
    brand_repository.get_all.return_value.ok_value = [test_brand]

    license_key_repository.get_by_id.return_value.is_err.return_value = False
    license_key_repository.get_by_id.return_value.ok_value = test_license_key
    license_key_repository.save.return_value.is_err.return_value = False
    license_key_repository.save.return_value.ok_value = test_license_key
    license_key_repository.get_all.return_value.is_err.return_value = False
    license_key_repository.get_all.return_value.ok_value = [test_license_key]

    service = AuthService(brand_repository, license_key_repository, logger)
    return service


@pytest.fixture
def test_app(auth_service):
    app = FastAPI()
    logger = LoggerAdapter()

    app.add_middleware(AuthMiddleware, auth_service=auth_service, logger=logger)

    @app.get("/api/v1/brands/test")
    async def brand_endpoint(request: Request):
        return {"brand_id": request.state.brand_id, "api_key": request.state.api_key}

    @app.get("/api/v1/users/license/activate")
    async def activate_endpoint(request: Request):
        return {"license_key": request.state.license_key, "license_key_id": request.state.license_key_id}

    @app.get("/api/v1/users/license/check-status")
    async def check_status_endpoint(request: Request):
        return {"license_key": request.state.license_key, "license_key_id": request.state.license_key_id}

    @app.get("/api/v1/users/license/deactivate")
    async def deactivate_endpoint(request: Request):
        return {"license_key": request.state.license_key, "license_key_id": request.state.license_key_id}

    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestAuthMiddlewareBrandAuth:

    def test_brand_auth_with_valid_key(self, client):
        response = client.get("/api/v1/brands/test", headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code == 200
        data = response.json()
        assert "brand_id" in data
        assert isinstance(data["brand_id"], str)
        assert data["api_key"] == TEST_API_KEY

    def test_brand_auth_missing_header(self, client):
        response = client.get("/api/v1/brands/test")

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-API-KEY header" in data["detail"]

    def test_brand_auth_invalid_key(self, client):
        response = client.get("/api/v1/brands/test", headers={"X-API-KEY": TEST_INVALID_API_KEY})

        assert response.status_code == 401
        data = response.json()
        assert "Invalid API key" in data["detail"]

    def test_brand_auth_empty_key(self, client):
        response = client.get("/api/v1/brands/test", headers={"X-API-KEY": ""})

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-API-KEY header" in data["detail"]


class TestAuthMiddlewareLicenseAuth:

    def test_license_auth_activate_with_valid_key(self, client):
        response = client.get("/api/v1/users/license/activate", headers={"X-LICENSE-KEY": TEST_LICENSE_KEY})

        assert response.status_code == 200
        data = response.json()
        assert data["license_key"] == TEST_LICENSE_KEY
        assert "license_key_id" in data
        assert isinstance(data["license_key_id"], str)

    def test_license_auth_check_status_with_valid_key(self, client):
        response = client.get("/api/v1/users/license/check-status", headers={"X-LICENSE-KEY": TEST_LICENSE_KEY})

        assert response.status_code == 200
        data = response.json()
        assert data["license_key"] == TEST_LICENSE_KEY
        assert "license_key_id" in data
        assert isinstance(data["license_key_id"], str)

    def test_license_auth_deactivate_with_valid_key(self, client):
        response = client.get("/api/v1/users/license/deactivate", headers={"X-LICENSE-KEY": TEST_LICENSE_KEY})

        assert response.status_code == 200
        data = response.json()
        assert data["license_key"] == TEST_LICENSE_KEY
        assert "license_key_id" in data
        assert isinstance(data["license_key_id"], str)

    def test_license_auth_activate_missing_header(self, client):
        response = client.get("/api/v1/users/license/activate")

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-LICENSE-KEY header" in data["detail"]

    def test_license_auth_check_status_missing_header(self, client):
        response = client.get("/api/v1/users/license/check-status")

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-LICENSE-KEY header" in data["detail"]

    def test_license_auth_deactivate_missing_header(self, client):
        response = client.get("/api/v1/users/license/deactivate")

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-LICENSE-KEY header" in data["detail"]

    def test_license_auth_activate_invalid_key(self, client):
        response = client.get("/api/v1/users/license/activate", headers={"X-LICENSE-KEY": TEST_INVALID_LICENSE_KEY})

        assert response.status_code == 401
        data = response.json()
        assert "Invalid license key" in data["detail"]

    def test_license_auth_check_status_invalid_key(self, client):
        response = client.get("/api/v1/users/license/check-status", headers={"X-LICENSE-KEY": TEST_INVALID_LICENSE_KEY})

        assert response.status_code == 401
        data = response.json()
        assert "Invalid license key" in data["detail"]

    def test_license_auth_deactivate_invalid_key(self, client):
        response = client.get("/api/v1/users/license/deactivate", headers={"X-LICENSE-KEY": TEST_INVALID_LICENSE_KEY})

        assert response.status_code == 401
        data = response.json()
        assert "Invalid license key" in data["detail"]


class TestAuthMiddlewarePublicEndpoints:

    def test_public_endpoint_no_auth(self, client):
        response = client.get("/public")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "public"

    def test_public_endpoint_with_auth_headers(self, client):
        response = client.get("/public", headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "public"


class TestAuthMiddlewareMultipleAuthTypes:

    def test_brand_endpoint_with_license_key_header(self, client):
        response = client.get("/api/v1/brands/test", headers={"X-LICENSE-KEY": TEST_LICENSE_KEY})

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-API-KEY header" in data["detail"]

    def test_license_endpoint_with_api_key_header(self, client):
        response = client.get("/api/v1/users/license/activate", headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code == 401
        data = response.json()
        assert "Missing X-LICENSE-KEY header" in data["detail"]
