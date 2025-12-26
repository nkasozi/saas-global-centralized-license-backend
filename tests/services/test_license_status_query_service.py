from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.activation import Activation, InstanceIDType
from src.core.models.licence import License
from src.core.models.licence_key import LicenseKey
from src.core.models.product import Product
from src.core.services.license_status_query_service import LicenseStatusQueryService


@pytest.fixture
def license_key_repository():
    return Mock()


@pytest.fixture
def license_repository():
    return Mock()


@pytest.fixture
def activation_repository():
    return Mock()


@pytest.fixture
def product_repository():
    return Mock()


@pytest.fixture
def logger():
    return Mock()


@pytest.fixture
def query_service(license_key_repository, license_repository, activation_repository, product_repository, logger):
    return LicenseStatusQueryService(
        license_key_repository=license_key_repository,
        license_repository=license_repository,
        activation_repository=activation_repository,
        product_repository=product_repository,
        logger=logger,
    )


@pytest.fixture
def valid_license_key():
    brand_id = str(uuid4())
    user_id = str(uuid4())
    key_result = LicenseKey.create(brand_id, user_id)
    return key_result.unwrap()


@pytest.fixture
def active_license():
    product_id = str(uuid4())
    license_result = License.create(product_id, datetime.now(timezone.utc) + timedelta(days=365))
    return license_result.unwrap()


@pytest.fixture
def valid_product():
    brand_id = str(uuid4())
    product_result = Product.create(brand_id, "Test Product", 100)
    return product_result.unwrap()


class TestLicenseStatusQueryService:
    def test_get_license_key_status_success(
        self,
        query_service,
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        valid_license_key,
        active_license,
        valid_product,
    ):
        valid_license_key.license_ids = [active_license.id]
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)
        license_repository.get_by_id.return_value = Ok(active_license)
        product_repository.get_by_id.return_value = Ok(valid_product)
        activation_repository.get_by_license_key_id.return_value = Ok([])

        result = query_service.get_license_key_status(valid_license_key.key_string)

        assert result.is_ok()
        status = result.unwrap()
        assert status["license_key_id"] == valid_license_key.id
        assert status["key_string"] == valid_license_key.key_string
        assert status["is_valid"] is True
        assert len(status["licenses"]) == 1
        assert len(status["activations"]) == 0

    def test_get_license_key_status_not_found(self, query_service, license_key_repository):
        license_key_repository.get_by_key_string.return_value = Err("License key not found")

        result = query_service.get_license_key_status("invalid-key")

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_get_license_key_status_with_activations(
        self,
        query_service,
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        valid_license_key,
        active_license,
        valid_product,
    ):
        valid_license_key.license_ids = [active_license.id]
        license_key_repository.get_by_key_string.return_value = Ok(valid_license_key)
        license_repository.get_by_id.return_value = Ok(active_license)
        product_repository.get_by_id.return_value = Ok(valid_product)

        activation_result = Activation.create(
            valid_license_key.id, InstanceIDType.URL, "https://example.com", "192.168.1.1"
        )
        activation = activation_result.unwrap()
        activation_repository.get_by_license_key_id.return_value = Ok([activation])

        result = query_service.get_license_key_status(valid_license_key.key_string)

        assert result.is_ok()
        status = result.unwrap()
        assert len(status["activations"]) == 1
        assert status["activations"][0]["instance_id"] == "https://example.com"

    def test_get_licenses_by_customer_email_success(self, query_service, license_key_repository):
        brand_id = str(uuid4())
        key1_result = LicenseKey.create(brand_id, str(uuid4()))
        key1 = key1_result.unwrap()
        key2_result = LicenseKey.create(brand_id, str(uuid4()))
        key2 = key2_result.unwrap()

        license_key_repository.get_by_brand_id.return_value = Ok([key1, key2])

        result = query_service.get_licenses_by_customer_email("customer@example.com", brand_id)

        assert result.is_ok()

    def test_get_licenses_by_customer_email_brand_not_found(self, query_service, license_key_repository):
        brand_id = str(uuid4())
        license_key_repository.get_by_brand_id.return_value = Err("Brand not found")

        result = query_service.get_licenses_by_customer_email("customer@example.com", brand_id)

        assert result.is_err()


@pytest.fixture
def product():
    brand_id = str(uuid4())
    product_result = Product.create(brand_id, "RankMath", 100)
    return product_result.unwrap()


@pytest.fixture
def mock_repositories():
    return {
        "license_key_repository": Mock(),
        "license_repository": Mock(),
        "activation_repository": Mock(),
        "product_repository": Mock(),
        "logger": Mock(),
    }


@pytest.fixture
def query_service_with_mocks(mock_repositories):
    return LicenseStatusQueryService(
        license_key_repository=mock_repositories["license_key_repository"],
        license_repository=mock_repositories["license_repository"],
        activation_repository=mock_repositories["activation_repository"],
        product_repository=mock_repositories["product_repository"],
        logger=mock_repositories["logger"],
    )


class TestLicenseStatusQueryServiceWithMocks:
    def test_get_licenses_by_customer_email(self, query_service_with_mocks, mock_repositories, valid_license_key):
        valid_license_key.license_ids = [str(uuid4())]
        mock_repositories["license_key_repository"].get_by_brand_id.return_value = Ok([valid_license_key])
        mock_repositories["license_key_repository"].get_by_key_string.return_value = Ok(valid_license_key)
        mock_repositories["activation_repository"].get_by_license_key_id.return_value = Ok([])
        mock_repositories["license_repository"].get_by_id.return_value = Ok(Mock())

        result = query_service_with_mocks.get_licenses_by_customer_email("user@example.com", valid_license_key.brand_id)

        assert result.is_ok()

    def test_get_all_brand_licenses_success(self, query_service_with_mocks, mock_repositories, valid_license_key):
        valid_license_key.license_ids = [str(uuid4())]
        mock_repositories["license_key_repository"].get_by_brand_id.return_value = Ok([valid_license_key])
        mock_repositories["license_key_repository"].get_by_key_string.return_value = Ok(valid_license_key)
        mock_repositories["activation_repository"].get_by_license_key_id.return_value = Ok([])
        mock_repositories["license_repository"].get_by_id.return_value = Ok(Mock())

        result = query_service_with_mocks.get_all_brand_licenses(valid_license_key.brand_id)

        assert result.is_ok()
        licenses_list = result.ok_value
        assert isinstance(licenses_list, list)

    def test_get_all_brand_licenses_multiple_keys(self, query_service_with_mocks, mock_repositories, valid_license_key):
        brand_id = valid_license_key.brand_id
        key2_result = LicenseKey.create(brand_id, str(uuid4()))
        key2 = key2_result.unwrap()
        valid_license_key.license_ids = [str(uuid4())]
        key2.license_ids = [str(uuid4())]

        mock_repositories["license_key_repository"].get_by_brand_id.return_value = Ok([valid_license_key, key2])
        mock_repositories["license_key_repository"].get_by_key_string.return_value = Ok(valid_license_key)
        mock_repositories["activation_repository"].get_by_license_key_id.return_value = Ok([])
        mock_repositories["license_repository"].get_by_id.return_value = Ok(Mock())

        result = query_service_with_mocks.get_all_brand_licenses(brand_id)

        assert result.is_ok()
        licenses_list = result.ok_value
        assert isinstance(licenses_list, list)

    def test_get_all_brand_licenses_brand_not_found(self, query_service_with_mocks, mock_repositories):
        brand_id = str(uuid4())
        mock_repositories["license_key_repository"].get_by_brand_id.return_value = Err("Brand not found")

        result = query_service_with_mocks.get_all_brand_licenses(brand_id)

        assert result.is_err()
        assert "not found" in result.err_value.lower()
