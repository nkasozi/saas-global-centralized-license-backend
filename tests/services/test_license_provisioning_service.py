from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.licence import License
from src.core.models.licence_key import LicenseKey
from src.core.models.product import Product
from src.core.services.license_provisioning_service import LicenseProvisioningService


@pytest.fixture
def license_repository() -> Mock:
    return Mock()


@pytest.fixture
def license_key_repository() -> Mock:
    return Mock()


@pytest.fixture
def product_repository() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def webhook_service() -> Mock:
    return Mock()


@pytest.fixture
def audit_service() -> Mock:
    return Mock()


@pytest.fixture
def provisioning_service(
    license_repository: Mock,
    license_key_repository: Mock,
    product_repository: Mock,
    webhook_service: Mock,
    audit_service: Mock,
    logger: Mock,
) -> LicenseProvisioningService:
    return LicenseProvisioningService(
        license_repository=license_repository,
        license_key_repository=license_key_repository,
        product_repository=product_repository,
        webhook_service=webhook_service,
        audit_service=audit_service,
        logger=logger,
    )


@pytest.fixture
def valid_product() -> Product:
    brand_id = str(uuid4())
    product_result = Product.create(brand_id, "TestProduct", 100)
    return product_result.unwrap()


@pytest.fixture
def future_date() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=365)


class TestLicenseProvisioningService:
    def test_provision_license_for_product_success(
        self,
        provisioning_service: LicenseProvisioningService,
        license_repository: Mock,
        license_key_repository: Mock,
        product_repository: Mock,
        valid_product: Product,
        future_date: datetime,
    ) -> None:
        brand_id = str(uuid4())
        end_product_user_id = str(uuid4())

        product_repository.get_by_id.return_value = Ok(valid_product)

        license_result = License.create(valid_product.id, future_date)
        license = license_result.unwrap()
        license_repository.save.return_value = Ok(license)

        key_result = LicenseKey.create(brand_id, end_product_user_id)
        license_key = key_result.unwrap()
        license_key.license_ids = [license.id]
        license_key_repository.save.return_value = Ok(license_key)

        result = provisioning_service.provision_license_for_product(
            product_id=valid_product.id,
            brand_id=brand_id,
            end_product_user_id=end_product_user_id,
            expiration_date=future_date,
        )

        assert result.is_ok()
        saved_license, saved_key = result.unwrap()
        assert saved_license.product_id == valid_product.id
        assert isinstance(saved_license.id, str)
        assert isinstance(saved_key.id, str)
        assert license.id in saved_key.license_ids

    def test_provision_license_product_not_found(self, provisioning_service, product_repository, future_date):
        brand_id = str(uuid4())
        product_id = str(uuid4())
        end_product_user_id = str(uuid4())

        product_repository.get_by_id.return_value = Err(f"Product {product_id} not found")

        result = provisioning_service.provision_license_for_product(
            product_id=product_id,
            brand_id=brand_id,
            end_product_user_id=end_product_user_id,
            expiration_date=future_date,
        )

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_provision_license_invalid_expiration_date(self, provisioning_service, product_repository, valid_product):
        brand_id = str(uuid4())
        end_product_user_id = str(uuid4())
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        product_repository.get_by_id.return_value = Ok(valid_product)

        result = provisioning_service.provision_license_for_product(
            product_id=valid_product.id,
            brand_id=brand_id,
            end_product_user_id=end_product_user_id,
            expiration_date=past_date,
        )

        assert result.is_err()

    def test_add_license_to_existing_key_success(
        self,
        provisioning_service,
        license_repository,
        license_key_repository,
        product_repository,
        valid_product,
        future_date,
    ):
        license_key_id = str(uuid4())

        key_result = LicenseKey.create(valid_product.brand_id, str(uuid4()))
        license_key = key_result.unwrap()
        license_key.id = license_key_id
        license_key_repository.get_by_id.return_value = Ok(license_key)

        product_repository.get_by_id.return_value = Ok(valid_product)

        license_result = License.create(valid_product.id, future_date)
        license = license_result.unwrap()
        license_repository.save.return_value = Ok(license)
        license_key_repository.save.return_value = Ok(license_key)

        result = provisioning_service.add_license_to_existing_key(
            license_key_id=license_key_id, product_id=valid_product.id, expiration_date=future_date
        )

        assert result.is_ok()
        saved_license = result.unwrap()
        assert saved_license.product_id == valid_product.id
        assert isinstance(saved_license.id, str)

    def test_add_license_key_not_found(self, provisioning_service, license_key_repository, future_date):
        license_key_id = str(uuid4())
        product_id = str(uuid4())

        license_key_repository.get_by_id.return_value = Err(f"License key {license_key_id} not found")

        result = provisioning_service.add_license_to_existing_key(
            license_key_id=license_key_id, product_id=product_id, expiration_date=future_date
        )

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_add_license_product_not_found(
        self, provisioning_service, license_key_repository, product_repository, future_date
    ):
        license_key_id = str(uuid4())
        product_id = str(uuid4())

        key_result = LicenseKey.create(str(uuid4()), str(uuid4()))
        license_key = key_result.unwrap()
        license_key.id = license_key_id
        license_key_repository.get_by_id.return_value = Ok(license_key)

        product_repository.get_by_id.return_value = Err(f"Product {product_id} not found")

        result = provisioning_service.add_license_to_existing_key(
            license_key_id=license_key_id, product_id=product_id, expiration_date=future_date
        )

        assert result.is_err()
        assert "not found" in result.unwrap_err()
