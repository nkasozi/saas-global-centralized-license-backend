from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.activation import Activation, InstanceIDType
from src.core.models.licence import License, LicenseStatus
from src.core.models.licence_key import LicenseKey
from src.core.models.product import Product
from src.core.services.license_activation_service import LicenseActivationService


@pytest.fixture
def activation_repository():
    return Mock()


@pytest.fixture
def license_key_repository():
    return Mock()


@pytest.fixture
def license_repository():
    return Mock()


@pytest.fixture
def product_repository():
    return Mock()


@pytest.fixture
def logger():
    return Mock()


@pytest.fixture
def webhook_service():
    return Mock()


@pytest.fixture
def audit_service():
    return Mock()


@pytest.fixture
def activation_service(
    activation_repository,
    license_key_repository,
    license_repository,
    product_repository,
    webhook_service,
    audit_service,
    logger,
):
    return LicenseActivationService(
        activation_repository=activation_repository,
        license_key_repository=license_key_repository,
        license_repository=license_repository,
        product_repository=product_repository,
        webhook_service=webhook_service,
        audit_service=audit_service,
        logger=logger,
    )


@pytest.fixture
def valid_license_key():
    brand_id = str(uuid4())
    user_id = str(uuid4())
    license_result = LicenseKey.create(brand_id, user_id)
    return license_result.unwrap()


@pytest.fixture
def active_license():
    product_id = str(uuid4())
    license_result = License.create(product_id, datetime.now(timezone.utc) + timedelta(days=365))
    return license_result.unwrap()


@pytest.fixture
def valid_product():
    brand_id = str(uuid4())
    product_result = Product.create(brand_id, "Test Product", 5)
    return product_result.unwrap()


class TestLicenseActivationService:
    def test_activate_license_for_instance_success(
        self,
        activation_service,
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        valid_license_key,
        active_license,
        valid_product,
    ):
        active_license.product_id = valid_product.id
        valid_license_key.license_ids = [active_license.id]
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)
        license_repository.get_by_id.return_value = Ok(active_license)
        product_repository.get_by_id.return_value = Ok(valid_product)

        activation_result = Activation.create(
            valid_license_key.id, InstanceIDType.URL, "https://example.com", "192.168.1.1"
        )
        activation = activation_result.unwrap()
        activation_repository.get_by_license_key_id_and_instance_id.return_value = Err("Not found")
        activation_repository.get_all.return_value = Ok([])
        activation_repository.save.return_value = Ok(activation)

        result = activation_service.activate_license_for_instance(
            license_key_string=valid_license_key.key_string,
            instance_id_type=InstanceIDType.URL,
            instance_id="https://example.com",
            ip_address="192.168.1.1",
        )

        assert result.is_ok()
        saved_activation = result.unwrap()
        assert isinstance(saved_activation.id, str)
        assert saved_activation.instance_id == "https://example.com"
        assert saved_activation.ip_address == "192.168.1.1"

    def test_activate_license_key_not_found(self, activation_service, license_key_repository):
        license_key_repository.get_by_key_string.return_value = Err("License key not found")

        result = activation_service.activate_license_for_instance(
            license_key_string="invalid-key",
            instance_id_type=InstanceIDType.URL,
            instance_id="https://example.com",
            ip_address="192.168.1.1",
        )

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_activate_license_already_activated(
        self,
        activation_service,
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        valid_license_key,
        active_license,
        valid_product,
    ):
        active_license.product_id = valid_product.id
        valid_license_key.license_ids = [active_license.id]
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)
        license_repository.get_by_id.return_value = Ok(active_license)
        product_repository.get_by_id.return_value = Ok(valid_product)

        activation_result = Activation.create(
            valid_license_key.id, InstanceIDType.URL, "https://example.com", "192.168.1.1"
        )
        existing_activation = activation_result.unwrap()
        activation_repository.get_by_license_key_id_and_instance_id.return_value = Ok(existing_activation)
        activation_repository.get_all.return_value = Ok([])

        result = activation_service.activate_license_for_instance(
            license_key_string=valid_license_key.key_string,
            instance_id_type=InstanceIDType.URL,
            instance_id="https://example.com",
            ip_address="192.168.1.1",
        )

        assert result.is_err()
        assert "already activated" in result.err_value

    def test_activate_license_exceeds_max_seats(
        self,
        activation_service,
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        valid_license_key,
        active_license,
        valid_product,
    ):
        active_license.product_id = valid_product.id
        valid_license_key.license_ids = [active_license.id]
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)
        license_repository.get_by_id.return_value = Ok(active_license)
        product_repository.get_by_id.return_value = Ok(valid_product)

        existing_activations = []
        for i in range(5):
            activation_result = Activation.create(
                valid_license_key.id, InstanceIDType.URL, f"https://example{i}.com", "192.168.1.1"
            )
            existing_activations.append(activation_result.unwrap())

        activation_repository.get_all.return_value = Ok(existing_activations)
        activation_repository.get_by_license_key_id_and_instance_id.return_value = Err("Not found")

        result = activation_service.activate_license_for_instance(
            license_key_string=valid_license_key.key_string,
            instance_id_type=InstanceIDType.URL,
            instance_id="https://example.com",
            ip_address="192.168.1.1",
        )

        assert result.is_err()

    def test_deactivate_instance_success(self, activation_service, activation_repository):
        activation_id = str(uuid4())
        activation_repository.get_by_id.return_value = Ok(Mock())
        activation_repository.delete_by_id.return_value = Ok(True)

        result = activation_service.deactivate_instance(activation_id)

        assert result.is_ok()
        assert result.unwrap() is True
        activation_repository.delete_by_id.assert_called_once_with(activation_id)

    def test_deactivate_instance_not_found(self, activation_service, activation_repository):
        activation_id = str(uuid4())
        activation_repository.get_by_id.return_value = Err(f"Activation {activation_id} not found")

        result = activation_service.deactivate_instance(activation_id)

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_activate_license_expired(
        self, activation_service, license_key_repository: Mock, license_repository: Mock, valid_license_key
    ):
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)

        expired_license = License(
            id=str(uuid4()),
            product_id=str(uuid4()),
            status=LicenseStatus.VALID,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc),
        )
        license_repository.get_by_id.return_value = Ok(expired_license)
        valid_license_key.license_ids = [expired_license.id]

        result = activation_service.activate_license_for_instance(
            license_key_string="abc123",
            instance_id_type=InstanceIDType.URL,
            instance_id="https://example.com",
            ip_address="192.168.1.1",
        )

        assert result.is_err()
        assert "not active" in result.err_value.lower()

    def test_activate_license_suspended(
        self, activation_service, license_key_repository: Mock, license_repository: Mock, valid_license_key
    ):
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)

        suspended_license = License(
            id=str(uuid4()),
            product_id=str(uuid4()),
            status=LicenseStatus.SUSPENDED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            created_at=datetime.now(timezone.utc),
        )
        license_repository.get_by_id.return_value = Ok(suspended_license)
        valid_license_key.license_ids = [suspended_license.id]

        result = activation_service.activate_license_for_instance(
            license_key_string="abc123",
            instance_id_type=InstanceIDType.URL,
            instance_id="https://example.com",
            ip_address="192.168.1.1",
        )

        assert result.is_err()
        assert "not active" in result.err_value.lower()
