from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.brand import Brand
from src.core.services.brand_manager import BrandManager


@pytest.fixture
def brand_repository() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def audit_service() -> Mock:
    return Mock()


@pytest.fixture
def brand_manager(brand_repository: Mock, audit_service: Mock, logger: Mock) -> BrandManager:
    return BrandManager(brand_repository, audit_service, logger)


@pytest.fixture
def test_brand() -> Brand:
    brand_result = Brand.create("Test Brand")
    return brand_result.unwrap()


class TestBrandManager:
    def test_create_brand_success(self, brand_manager: BrandManager, brand_repository: Mock) -> None:
        brand_result = Brand.create("New Brand")
        brand = brand_result.unwrap()
        brand_repository.save.return_value = Ok(brand)

        result = brand_manager.create_brand("New Brand")

        assert result.is_ok()
        assert result.unwrap().brand_name == "New Brand"
        assert isinstance(result.unwrap().id, str)
        brand_repository.save.assert_called_once()

    def test_create_brand_invalid_name_empty(self, brand_manager: BrandManager) -> None:
        result = brand_manager.create_brand("")

        assert result.is_err()
        assert "Brand name" in result.unwrap_err()

    def test_create_brand_invalid_name_whitespace(self, brand_manager: BrandManager) -> None:
        result = brand_manager.create_brand("   ")

        assert result.is_err()

    def test_get_brand_by_id_success(
        self, brand_manager: BrandManager, brand_repository: Mock, test_brand: Brand
    ) -> None:
        brand_id = str(uuid4())
        test_brand.id = brand_id
        brand_repository.get_by_id.return_value = Ok(test_brand)

        result = brand_manager.get_brand_by_id(brand_id)

        assert result.is_ok()
        assert result.unwrap().id == brand_id
        brand_repository.get_by_id.assert_called_once_with(brand_id)

    def test_get_brand_by_id_not_found(self, brand_manager: BrandManager, brand_repository: Mock) -> None:
        brand_id = str(uuid4())
        brand_repository.get_by_id.return_value = Err("Brand not found")

        result = brand_manager.get_brand_by_id(brand_id)

        assert result.is_err()
        brand_repository.get_by_id.assert_called_once_with(brand_id)

    def test_get_brand_by_id_with_empty_id(self, brand_manager: BrandManager, brand_repository: Mock) -> None:
        brand_repository.get_by_id.return_value = Err("Entity with id  not found")

        result = brand_manager.get_brand_by_id("")

        assert result.is_err()

    def test_get_all_brands_success(
        self, brand_manager: BrandManager, brand_repository: Mock, test_brand: Brand
    ) -> None:
        test_brand.id = str(uuid4())
        brand_result_2 = Brand.create("Another Brand")
        another_brand = brand_result_2.unwrap()
        another_brand.id = str(uuid4())

        brand_repository.get_all.return_value = Ok([test_brand, another_brand])

        result = brand_manager.get_all_brands()

        assert result.is_ok()
        brands = result.unwrap()
        assert len(brands) == 2
        assert all(isinstance(b.id, str) for b in brands)
        brand_repository.get_all.assert_called_once()

    def test_get_all_brands_empty(self, brand_manager: BrandManager, brand_repository: Mock) -> None:
        brand_repository.get_all.return_value = Ok([])

        result = brand_manager.get_all_brands()

        assert result.is_ok()
        assert result.unwrap() == []

    def test_list_brands_empty(self, brand_manager: BrandManager, brand_repository: Mock) -> None:
        brand_repository.get_all.return_value = Ok([])

        result = brand_manager.get_all_brands()

        assert result.is_ok()
        assert len(result.unwrap()) == 0

    def test_brand_manager_creates_unique_brands(self, brand_manager: BrandManager, brand_repository: Mock) -> None:
        brand1_result = Brand.create("Brand 1")
        brand2_result = Brand.create("Brand 2")
        brand1 = brand1_result.unwrap()
        brand2 = brand2_result.unwrap()

        brand_repository.save.side_effect = [Ok(brand1), Ok(brand2)]

        result1 = brand_manager.create_brand("Brand 1")
        result2 = brand_manager.create_brand("Brand 2")

        assert result1.is_ok()
        assert result2.is_ok()
        id1 = result1.unwrap().id
        id2 = result2.unwrap().id
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
