from typing import List

from result import Err, Ok, Result

from src.core.models.product import Product
from src.infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository


class ProductRepository(InMemoryRepository[Product]):
    def get_by_brand_id(self, brand_id: str) -> Result[List[Product], str]:
        products_for_brand = [p for p in self._storage.values() if p.brand_id == brand_id]
        return Ok(products_for_brand)

    def get_by_brand_id_and_name(self, brand_id: str, product_name: str) -> Result[Product, str]:
        matching_products = [
            p for p in self._storage.values() if p.brand_id == brand_id and p.product_name == product_name
        ]

        if not matching_products:
            return Err(f"Product '{product_name}' not found for brand {brand_id}")

        return Ok(matching_products[0])
