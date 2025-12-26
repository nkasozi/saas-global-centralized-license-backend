from result import Err, Ok, Result

from src.core.models.brand import Brand
from src.infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository


class BrandRepository(InMemoryRepository[Brand]):
    def get_by_name(self, brand_name: str) -> Result[Brand, str]:
        matching_brands = [b for b in self._storage.values() if b.brand_name == brand_name]

        if not matching_brands:
            return Err(f"Brand with name '{brand_name}' not found")

        return Ok(matching_brands[0])

    def get_by_api_hash_key(self, api_hash_key: str) -> Result[Brand, str]:
        matching_brands = [b for b in self._storage.values() if b.api_hash_key == api_hash_key]

        if not matching_brands:
            return Err("Brand with API hash key not found")

        return Ok(matching_brands[0])
