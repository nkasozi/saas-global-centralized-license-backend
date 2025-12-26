from result import Err, Ok, Result

from src.core.models.brand import Brand
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class BrandRepository(FileRepository[Brand]):
    def __init__(self):
        super().__init__("data/brands.json", Brand)

    def get_by_name(self, brand_name: str) -> Result[Brand, str]:
        all_brands_result = self.get_all()
        if all_brands_result.is_err():
            return all_brands_result

        matching_brands = [b for b in all_brands_result.ok_value if b.brand_name == brand_name]

        if not matching_brands:
            return Err(f"Brand with name '{brand_name}' not found")

        return Ok(matching_brands[0])

    def get_by_api_hash_key(self, api_hash_key: str) -> Result[Brand, str]:
        all_brands_result = self.get_all()
        if all_brands_result.is_err():
            return all_brands_result

        matching_brands = [b for b in all_brands_result.ok_value if b.api_hash_key == api_hash_key]

        if not matching_brands:
            return Err("Brand with API hash key not found")

        return Ok(matching_brands[0])
