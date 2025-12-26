import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_activation_repository,
    get_audit_log_repository,
    get_brand_repository,
    get_license_key_repository,
    get_license_repository,
    get_logger,
    get_product_repository,
    get_webhook_repository,
)
from src.infrastructure.logging.logger_adapter import LoggerAdapter
from infrastructure.persistence.in_memory_db.activation_repository import ActivationRepository
from infrastructure.persistence.in_memory_db.audit_log_repository import AuditLogRepository
from infrastructure.persistence.in_memory_db.brand_repository import BrandRepository
from infrastructure.persistence.in_memory_db.end_product_user_repository import EndProductUserRepository
from infrastructure.persistence.in_memory_db.license_key_repository import LicenseKeyRepository
from infrastructure.persistence.in_memory_db.license_repository import LicenseRepository
from infrastructure.persistence.in_memory_db.product_repository import ProductRepository
from infrastructure.persistence.in_memory_db.webhook_repository import WebhookRepository
from src.main import app


@pytest.fixture(scope="function")
def test_brand_repository():
    return BrandRepository()


@pytest.fixture(scope="function")
def test_product_repository():
    return ProductRepository()


@pytest.fixture(scope="function")
def test_license_repository():
    return LicenseRepository()


@pytest.fixture(scope="function")
def test_license_key_repository():
    return LicenseKeyRepository()


@pytest.fixture(scope="function")
def test_activation_repository():
    return ActivationRepository()


@pytest.fixture(scope="function")
def test_user_repository():
    return EndProductUserRepository()


@pytest.fixture(scope="function")
def test_audit_log_repository():
    return AuditLogRepository()


@pytest.fixture(scope="function")
def test_webhook_repository():
    return WebhookRepository()


@pytest.fixture(scope="function")
def test_logger():
    return LoggerAdapter()


@pytest.fixture
def client(
    test_brand_repository,
    test_product_repository,
    test_license_repository,
    test_license_key_repository,
    test_activation_repository,
    test_user_repository,
    test_audit_log_repository,
    test_webhook_repository,
    test_logger,
):
    app.dependency_overrides[get_brand_repository] = lambda: test_brand_repository
    app.dependency_overrides[get_product_repository] = lambda: test_product_repository
    app.dependency_overrides[get_license_repository] = lambda: test_license_repository
    app.dependency_overrides[get_license_key_repository] = lambda: test_license_key_repository
    app.dependency_overrides[get_activation_repository] = lambda: test_activation_repository
    app.dependency_overrides[get_audit_log_repository] = lambda: test_audit_log_repository
    app.dependency_overrides[get_webhook_repository] = lambda: test_webhook_repository
    app.dependency_overrides[get_logger] = lambda: test_logger

    yield TestClient(app)

    app.dependency_overrides.clear()


