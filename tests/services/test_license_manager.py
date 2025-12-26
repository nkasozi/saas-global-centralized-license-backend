from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.licence import License, LicenseStatus
from src.core.services.licence_manager import LicenseManager


@pytest.fixture
def license_repository() -> Mock:
    return Mock()


@pytest.fixture
def license_key_repository() -> Mock:
    return Mock()


@pytest.fixture
def user_repository() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def audit_service() -> Mock:
    return Mock()


@pytest.fixture
def license_manager(
    license_repository: Mock, license_key_repository: Mock, user_repository: Mock, audit_service: Mock, logger: Mock
) -> LicenseManager:
    return LicenseManager(license_repository, license_key_repository, user_repository, audit_service, logger)


@pytest.fixture
def test_license() -> License:
    product_id = str(uuid4())
    expiration_date = datetime.now(timezone.utc) + timedelta(days=365)
    license_result = License.create(product_id, expiration_date)
    return license_result.unwrap()


class TestLicenseManager:
    def test_create_license_success(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        product_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        license_result = License.create(product_id, expires_at)
        license = license_result.unwrap()
        license_repository.save.return_value = Ok(license)

        result = license_manager.create_license(product_id, expires_at)

        assert result.is_ok()
        created = result.unwrap()
        assert created.product_id == product_id
        assert created.status == LicenseStatus.VALID
        assert isinstance(created.id, str)
        license_repository.save.assert_called_once()

    def test_create_license_invalid_product_id_empty(self, license_manager: LicenseManager) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        result = license_manager.create_license("", expires_at)

        assert result.is_err()
        assert "Product ID" in result.unwrap_err()

    def test_create_license_invalid_expiration_date_past(self, license_manager: LicenseManager) -> None:
        product_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        result = license_manager.create_license(product_id, expires_at)

        assert result.is_err()
        assert "future" in result.unwrap_err().lower()

    def test_get_license_by_id_success(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.get_license_by_id(test_license.id)

        assert result.is_ok()
        assert result.unwrap().id == test_license.id
        license_repository.get_by_id.assert_called_once_with(test_license.id)

    def test_get_license_by_id_not_found(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        license_id = str(uuid4())
        license_repository.get_by_id.return_value = Err(f"Entity with id {license_id} not found")

        result = license_manager.get_license_by_id(license_id)

        assert result.is_err()

    def test_suspend_license_success(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        license_repository.get_by_id.return_value = Ok(test_license)
        license_repository.save.return_value = Ok(test_license)

        result = license_manager.suspend_license(test_license.id)

        assert result.is_ok()
        suspended = result.unwrap()
        assert suspended.status == LicenseStatus.SUSPENDED
        license_repository.save.assert_called_once()

    def test_suspend_license_not_found(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        license_id = str(uuid4())
        license_repository.get_by_id.return_value = Err(f"Entity with id {license_id} not found")

        result = license_manager.suspend_license(license_id)

        assert result.is_err()

    def test_resume_license_success(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        test_license.status = LicenseStatus.SUSPENDED
        license_repository.get_by_id.return_value = Ok(test_license)
        license_repository.save.return_value = Ok(test_license)

        result = license_manager.resume_license(test_license.id)

        assert result.is_ok()
        resumed = result.unwrap()
        assert resumed.status == LicenseStatus.VALID
        license_repository.save.assert_called_once()

    def test_resume_license_not_found(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        license_id = str(uuid4())
        license_repository.get_by_id.return_value = Err(f"Entity with id {license_id} not found")

        result = license_manager.resume_license(license_id)

        assert result.is_err()

    def test_cancel_license_success(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        license_repository.get_by_id.return_value = Ok(test_license)
        license_repository.save.return_value = Ok(test_license)

        result = license_manager.cancel_license(test_license.id)

        assert result.is_ok()
        cancelled = result.unwrap()
        assert cancelled.status == LicenseStatus.CANCELLED
        license_repository.save.assert_called_once()

    def test_cancel_license_not_found(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        license_id = str(uuid4())
        license_repository.get_by_id.return_value = Err(f"Entity with id {license_id} not found")

        result = license_manager.cancel_license(license_id)

        assert result.is_err()

    def test_renew_license_success(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        new_expiration = datetime.now(timezone.utc) + timedelta(days=180)
        license_repository.get_by_id.return_value = Ok(test_license)
        license_repository.save.return_value = Ok(test_license)

        result = license_manager.renew_license(test_license.id, new_expiration)

        assert result.is_ok()
        renewed = result.unwrap()
        assert renewed.expires_at == new_expiration
        license_repository.save.assert_called_once()

    def test_renew_license_invalid_expiration_date_past(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        new_expiration = datetime.now(timezone.utc) - timedelta(days=1)
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.renew_license(test_license.id, new_expiration)

        assert result.is_err()
        assert "future" in result.unwrap_err().lower()

    def test_renew_license_not_found(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        license_id = str(uuid4())
        new_expiration = datetime.now(timezone.utc) + timedelta(days=180)
        license_repository.get_by_id.return_value = Err(f"Entity with id {license_id} not found")

        result = license_manager.renew_license(license_id, new_expiration)

        assert result.is_err()

    def test_renew_license_invalid_date(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.renew_license(test_license.id, past_date)

        assert result.is_err()
        assert "future" in result.unwrap_err().lower()

    def test_renew_cancelled_license(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        test_license.status = LicenseStatus.CANCELLED
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.renew_license(test_license.id, datetime.now(timezone.utc) + timedelta(days=365))

        assert result.is_err()

    def test_cancel_already_cancelled_license(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        test_license.status = LicenseStatus.CANCELLED
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.cancel_license(test_license.id)

        assert result.is_err()

    def test_get_license_status_valid(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.get_license_by_id(test_license.id)

        assert result.is_ok()
        license = result.unwrap()
        assert license.status == LicenseStatus.VALID

    def test_get_license_status_suspended(
        self, license_manager: LicenseManager, license_repository: Mock, test_license: License
    ) -> None:
        test_license.status = LicenseStatus.SUSPENDED
        license_repository.get_by_id.return_value = Ok(test_license)

        result = license_manager.get_license_by_id(test_license.id)

        assert result.is_ok()
        license = result.unwrap()
        assert license.status == LicenseStatus.SUSPENDED

    def test_get_license_status_expired(self, license_manager: LicenseManager, license_repository: Mock) -> None:
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        expired_license_result = License.create("1", future_date)
        expired_license = expired_license_result.unwrap()
        expired_license.id = "1"
        expired_license.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        license_repository.get_by_id.return_value = Ok(expired_license)

        result = license_manager.get_license_by_id(expired_license.id)

        assert result.is_ok()
        license = result.unwrap()
        assert not license.is_active()
