from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.core.models.brand import Brand
from src.core.models.licence_key import LicenseKey
from src.infrastructure.auth.auth_service import AuthService
from src.infrastructure.logging.logger_adapter import LoggerAdapter


@pytest.fixture
def brand_repository() -> Mock:
    return Mock()


@pytest.fixture
def license_key_repository() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> LoggerAdapter:
    return LoggerAdapter()


@pytest.fixture
def auth_service(brand_repository: Mock, license_key_repository: Mock, logger: LoggerAdapter) -> AuthService:
    return AuthService(brand_repository, license_key_repository, logger)


def create_test_brand(brand_id: str, api_key: str) -> Brand:
    result = Brand.create("Test Brand")
    brand = result.ok_value
    brand.id = brand_id
    brand.api_hash_key = api_key
    return brand


def create_test_license_key(license_key_id: str, brand_id: str, key_string: str) -> LicenseKey:
    result = LicenseKey.create(brand_id, str(uuid4()))
    license_key = result.ok_value
    license_key.id = license_key_id
    license_key.key_string = key_string
    return license_key


class TestAuthServiceBrandKeyValidation:
    def test_validate_nonexistent_brand_api_key(self, auth_service: AuthService, brand_repository: Mock) -> None:
        brand_repository.get_all.return_value.is_err.return_value = False
        brand_repository.get_all.return_value.ok_value = []

        result = auth_service.validate_brand_api_key("nonexistent-key")

        assert result.is_err()
        assert "not found" in result.err_value.lower()

    def test_validate_empty_brand_api_key(self, auth_service: AuthService) -> None:
        result = auth_service.validate_brand_api_key("")

        assert result.is_err()


class TestAuthServiceLicenseKeyValidation:

    def test_validate_nonexistent_license_key(self, auth_service: AuthService, license_key_repository: Mock) -> None:
        license_key_repository.get_all.return_value.is_err.return_value = False
        license_key_repository.get_all.return_value.ok_value = []

        result = auth_service.validate_license_key("nonexistent-license-key")

        assert result.is_err()
        assert "not found" in result.err_value.lower()

    def test_validate_empty_license_key(self, auth_service: AuthService) -> None:
        result = auth_service.validate_license_key("")

        assert result.is_err()
