from src.core.models.end_product_user import EndProductUser
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class EndProductUserRepository(FileRepository[EndProductUser]):
    def __init__(self):
        super().__init__("data/end_product_users.json", EndProductUser)

    def get_by_brand_id(self, brand_id: str):
        all_users_result = self.get_all()
        if all_users_result.is_err():
            return all_users_result

        brand_users = [u for u in all_users_result.ok_value if u.brand_id == brand_id]
        return all_users_result.__class__(brand_users)
