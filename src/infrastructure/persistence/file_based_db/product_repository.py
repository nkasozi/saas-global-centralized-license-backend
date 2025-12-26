from result import Err, Ok, Result

from src.core.models.product import Product
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class ProductRepository(FileRepository[Product]):
    def __init__(self):
        super().__init__("data/products.json", Product)

    def get_by_brand_id(self, brand_id: str) -> Result[list[Product], str]:
        all_products_result = self.get_all()
        if all_products_result.is_err():
            return all_products_result

        brand_products = [p for p in all_products_result.ok_value if p.brand_id == brand_id]
        return Ok(brand_products)

    def get_by_name(self, product_name: str) -> Result[Product, str]:
        all_products_result = self.get_all()
        if all_products_result.is_err():
            return all_products_result

        matching_products = [p for p in all_products_result.ok_value if p.product_name == product_name]

        if not matching_products:
            return Err(f"Product with name '{product_name}' not found")

        return Ok(matching_products[0])
