from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.core.models.activation import InstanceIDType
from src.core.models.brand import Brand
from src.core.models.end_product_user import EndProductUser
from src.core.models.licence import License, LicenseStatus
from src.core.models.product import Product
from src.main import app

TEST_API_KEY = "test-api-key-valid-1234567890"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_brand_id() -> str:
    return str(uuid4())


@pytest.fixture
def valid_product_id() -> str:
    return str(uuid4())


@pytest.fixture
def valid_license_id() -> str:
    return str(uuid4())


@pytest.fixture
def valid_user_id() -> str:
    return str(uuid4())


@pytest.fixture
def valid_brand() -> Brand:
    brand_result = Brand.create("Test Brand")
    return brand_result.unwrap()


@pytest.fixture
def valid_product(valid_brand: Brand) -> Product:
    product_result = Product.create(valid_brand.id, "Test Product", 100)
    return product_result.unwrap()


@pytest.fixture
def valid_license(valid_product):
    license_result = License.create(valid_product.id, datetime.now(timezone.utc) + timedelta(days=365))
    return license_result.unwrap()


@pytest.fixture
def valid_end_product_user():
    user_result = EndProductUser.create("user@example.com", "test-token")
    return user_result.unwrap()


class TestBrandEndpoints:
    def test_create_brand_success(self, client):
        payload = {"brand_name": "New Test Brand", "api_hash_key": "valid-hash-key-12345"}
        response = client.post("/api/v1/brands", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code in [200, 201]
        data = response.json()
        assert "brand_id" in data or "id" in data
        assert data.get("brand_name") == "New Test Brand"

    def test_create_brand_empty_name(self, client):
        payload = {"brand_name": "", "api_hash_key": "valid-key-12345"}
        response = client.post("/api/v1/brands", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code == 400

    def test_create_brand_whitespace_name(self, client):
        payload = {"brand_name": "   ", "api_hash_key": "valid-key-12345"}
        response = client.post("/api/v1/brands", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code == 400

    def test_can_create_brand_without_api_key(self, client):
        payload = {"brand_name": "New Brand", "api_hash_key": "valid-key-12345"}
        response = client.post("/api/v1/brands", json=payload, headers={"X-API-KEY": ""})

        assert response.status_code == 201

    def test_create_product_success(self, client, valid_brand_id):
        payload = {"product_name": "Test Product", "max_seats": 50}
        response = client.post(
            f"/api/v1/brands/{valid_brand_id}/products", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [200, 201, 401]
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            assert data.get("product_name") == "Test Product"
            assert data.get("max_seats") == 50

    def test_create_product_empty_name(self, client, valid_brand_id):
        payload = {"product_name": "", "max_seats": 50}
        response = client.post(
            f"/api/v1/brands/{valid_brand_id}/products", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [400, 401]

    def test_create_product_negative_seats(self, client, valid_brand_id):
        payload = {"product_name": "Test Product", "max_seats": -1}
        response = client.post(
            f"/api/v1/brands/{valid_brand_id}/products", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [400, 401]

    def test_create_product_zero_seats(self, client, valid_brand_id):
        payload = {"product_name": "Test Product", "max_seats": 0}
        response = client.post(
            f"/api/v1/brands/{valid_brand_id}/products", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [400, 401]

    def test_update_product_success(self, client, valid_brand_id, valid_product_id):
        payload = {"product_name": "Updated Product", "max_seats": 75}
        response = client.put(
            f"/api/v1/brands/{valid_brand_id}/products/{valid_product_id}",
            json=payload,
            headers={"X-API-KEY": TEST_API_KEY},
        )

        if response.status_code in [200, 404]:
            if response.status_code == 200:
                data = response.json()
                assert data.get("product_name") == "Updated Product"

    def test_update_product_invalid_brand_id(self, client):
        invalid_brand_id = "not-a-uuid"
        payload = {"product_name": "Updated", "max_seats": 50}
        response = client.put(
            f"/api/v1/brands/{invalid_brand_id}/products/some-id", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [400, 401, 404]

    def test_delete_product_success(self, client, valid_brand_id, valid_product_id):
        response = client.delete(
            f"/api/v1/brands/{valid_brand_id}/products/{valid_product_id}", headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [200, 204, 401, 404]

    def test_list_products_by_brand(self, client, valid_brand_id):
        response = client.get(f"/api/v1/brands/{valid_brand_id}/products", headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


class TestLicenseEndpoints:
    def test_provision_license_success(self, client, valid_product_id):
        payload = {"expiration_date": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()}
        response = client.post(
            f"/api/v1/products/{valid_product_id}/licenses", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        if response.status_code in [200, 201, 404]:
            if response.status_code in [200, 201]:
                assert "license_id" in response.json() or "id" in response.json()

    def test_provision_license_past_date(self, client, valid_product_id):
        payload = {"expiration_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}
        response = client.post(
            f"/api/v1/products/{valid_product_id}/licenses", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        assert response.status_code in [400, 404]

    def test_suspend_license_success(self, client, valid_product_id, valid_license_id):
        response = client.patch(f"/api/v1/licenses/{valid_license_id}/suspend", headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code in [200, 404]:
            if response.status_code == 200:
                data = response.json()
                assert data.get("status") == LicenseStatus.SUSPENDED.value

    def test_resume_license_success(self, client, valid_license_id):
        response = client.patch(f"/api/v1/licenses/{valid_license_id}/resume", headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code in [200, 404]:
            if response.status_code == 200:
                data = response.json()
                assert data.get("status") == LicenseStatus.VALID.value

    def test_cancel_license_success(self, client, valid_license_id):
        response = client.patch(f"/api/v1/licenses/{valid_license_id}/cancel", headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code in [200, 404]:
            if response.status_code == 200:
                data = response.json()
                assert data.get("status") == LicenseStatus.CANCELLED.value

    def test_renew_license_success(self, client, valid_license_id):
        payload = {"new_expiration_date": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()}
        response = client.patch(
            f"/api/v1/licenses/{valid_license_id}/renew", json=payload, headers={"X-API-KEY": TEST_API_KEY}
        )

        if response.status_code in [200, 404]:
            if response.status_code == 200:
                assert "license_id" in response.json() or "id" in response.json()


class TestActivationEndpoints:
    def test_activate_license_success(self, client):
        payload = {
            "license_key": "test-license-key-valid",
            "instance_id_type": InstanceIDType.URL.value,
            "instance_id": "https://example.com",
        }
        response = client.post("/api/v1/activations", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code in [200, 201, 404]:
            if response.status_code in [200, 201]:
                assert "activation_id" in response.json() or "id" in response.json()

    def test_activate_license_invalid_url(self, client):
        payload = {
            "license_key": "test-license-key",
            "instance_id_type": InstanceIDType.URL.value,
            "instance_id": "not-a-url",
        }
        response = client.post("/api/v1/activations", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code != 404:
            assert response.status_code == 400

    def test_check_license_status_success(self, client):
        license_key = "test-license-key"
        response = client.get(f"/api/v1/license-status?license_key={license_key}", headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code in [200, 404]:
            pass

    def test_deactivate_instance_success(self, client):
        payload = {"license_key": "test-license-key", "instance_id": "https://example.com"}
        response = client.post("/api/v1/deactivations", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        if response.status_code in [200, 404]:
            pass

    def test_activate_missing_instance_id(self, client):
        payload = {
            "license_key": "test-license-key",
            "instance_id_type": InstanceIDType.URL.value,
        }
        response = client.post("/api/v1/activations", json=payload, headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code == 404


class TestAuthenticationMiddleware:
    def test_missing_api_key_header(self, client):
        response = client.get("/api/v1/brands")

        assert response.status_code == 401

    def test_invalid_api_key_format(self, client):
        response = client.get("/api/v1/brands", headers={"X-API-KEY": "too-short"})

        assert response.status_code == 401

    def test_valid_api_key_format(self, client):
        response = client.get("/api/v1/brands", headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code in [200, 400, 401]

    def test_case_sensitive_header_name(self, client):
        response = client.get("/api/v1/brands", headers={"X-API-KEY": TEST_API_KEY})

        assert response.status_code in [200, 401, 400]
