from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.product import Product
from src.core.services.product_manager import ProductManager


@pytest.fixture
def product_repository() -> Mock:
    return Mock()


@pytest.fixture
def audit_service() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def product_manager(product_repository: Mock, audit_service: Mock, logger: Mock) -> ProductManager:
    return ProductManager(product_repository, audit_service, logger)


@pytest.fixture
def test_product() -> Product:
    product_result = Product.create(str(uuid4()), "Test Product", 100)
    return product_result.unwrap()


class TestProductManager:
    def test_create_product_success(self, product_manager: ProductManager, product_repository: Mock) -> None:
        brand_id = str(uuid4())
        product_result = Product.create(brand_id, "New Product", 50)
        product = product_result.unwrap()
        product_repository.save.return_value = Ok(product)

        result = product_manager.create_product(brand_id, "New Product", 50)

        assert result.is_ok()
        created = result.unwrap()
        assert created.product_name == "New Product"
        assert created.max_seats == 50
        assert created.brand_id == brand_id
        assert isinstance(created.id, str)
        product_repository.save.assert_called_once()

    def test_create_product_invalid_brand_id_empty(self, product_manager: ProductManager) -> None:
        result = product_manager.create_product("", "Product Name", 50)

        assert result.is_err()
        assert "Brand ID" in result.unwrap_err()

    def test_create_product_invalid_product_name_empty(self, product_manager: ProductManager) -> None:
        brand_id = str(uuid4())
        result = product_manager.create_product(brand_id, "", 50)

        assert result.is_err()
        assert "Product name" in result.unwrap_err()

    def test_create_product_invalid_product_name_whitespace(self, product_manager: ProductManager) -> None:
        brand_id = str(uuid4())
        result = product_manager.create_product(brand_id, "   ", 50)

        assert result.is_err()

    def test_create_product_invalid_max_seats_negative(self, product_manager: ProductManager) -> None:
        brand_id = str(uuid4())
        result = product_manager.create_product(brand_id, "Product", -1)

        assert result.is_err()
        assert "Max seats" in result.unwrap_err()

    def test_create_product_invalid_max_seats_zero(self, product_manager: ProductManager) -> None:
        brand_id = str(uuid4())
        result = product_manager.create_product(brand_id, "Product", 0)

        assert result.is_ok()

    def test_get_product_by_id_success(
        self, product_manager: ProductManager, product_repository: Mock, test_product: Product
    ) -> None:
        product_id = str(uuid4())
        test_product.id = product_id
        product_repository.get_by_id.return_value = Ok(test_product)

        result = product_manager.get_product_by_id(product_id)

        assert result.is_ok()
        assert result.unwrap().id == product_id
        product_repository.get_by_id.assert_called_once_with(product_id)

    def test_get_product_by_id_not_found(self, product_manager: ProductManager, product_repository: Mock) -> None:
        product_id = str(uuid4())
        product_repository.get_by_id.return_value = Err(f"Entity with id {product_id} not found")

        result = product_manager.get_product_by_id(product_id)

        assert result.is_err()

    def test_get_products_by_brand_id_success(self, product_manager: ProductManager, product_repository: Mock) -> None:
        brand_id = str(uuid4())
        product1_result = Product.create(brand_id, "Product 1", 100)
        product2_result = Product.create(brand_id, "Product 2", 50)
        products = [product1_result.unwrap(), product2_result.unwrap()]
        product_repository.get_by_brand_id.return_value = Ok(products)

        result = product_manager.get_products_by_brand_id(brand_id)

        assert result.is_ok()
        prods = result.unwrap()
        assert len(prods) == 2
        assert all(p.brand_id == brand_id for p in prods)
        product_repository.get_by_brand_id.assert_called_once_with(brand_id)

    def test_get_products_by_brand_id_empty(self, product_manager: ProductManager, product_repository: Mock) -> None:
        brand_id = str(uuid4())
        product_repository.get_by_brand_id.return_value = Ok([])

        result = product_manager.get_products_by_brand_id(brand_id)

        assert result.is_ok()
        assert result.unwrap() == []

    def test_update_product_success(
        self, product_manager: ProductManager, product_repository: Mock, test_product: Product
    ) -> None:
        product_id = str(uuid4())
        test_product.id = product_id
        product_repository.get_by_id.return_value = Ok(test_product)
        product_repository.save.return_value = Ok(test_product)

        result = product_manager.update_product(product_id, "Updated Name", 200)

        assert result.is_ok()
        updated = result.unwrap()
        assert updated.product_name == "Updated Name"
        assert updated.max_seats == 200

    def test_update_product_name_only(
        self, product_manager: ProductManager, product_repository: Mock, test_product: Product
    ) -> None:
        product_id = str(uuid4())
        test_product.id = product_id
        product_repository.get_by_id.return_value = Ok(test_product)
        product_repository.save.return_value = Ok(test_product)

        result = product_manager.update_product(product_id, "New Name", None)

        assert result.is_ok()
        updated = result.unwrap()
        assert updated.product_name == "New Name"

    def test_update_product_seats_only(
        self, product_manager: ProductManager, product_repository: Mock, test_product: Product
    ) -> None:
        product_id = str(uuid4())
        old_name = test_product.product_name
        test_product.id = product_id
        product_repository.get_by_id.return_value = Ok(test_product)
        product_repository.save.return_value = Ok(test_product)

        result = product_manager.update_product(product_id, None, 500)

        assert result.is_ok()
        updated = result.unwrap()
        assert updated.product_name == old_name

    def test_update_product_not_found(self, product_manager: ProductManager, product_repository: Mock) -> None:
        product_id = str(uuid4())
        product_repository.get_by_id.return_value = Err(f"Entity with id {product_id} not found")

        result = product_manager.update_product(product_id, "New Name", 100)

        assert result.is_err()

    def test_delete_product_success(
        self, product_manager: ProductManager, product_repository: Mock, test_product: Product
    ) -> None:
        product_id = str(uuid4())
        test_product.id = product_id
        product_repository.get_by_id.return_value = Ok(test_product)
        product_repository.delete.return_value = Ok(product_id)

        result = product_manager.delete_product(product_id)

        assert result.is_ok()
        product_repository.delete.assert_called_once_with(product_id)

    def test_delete_product_not_found(self, product_manager: ProductManager, product_repository: Mock) -> None:
        product_id = str(uuid4())
        product_repository.get_by_id.return_value = Err(f"Entity with id {product_id} not found")

        result = product_manager.delete_product(product_id)

        assert result.is_err()
