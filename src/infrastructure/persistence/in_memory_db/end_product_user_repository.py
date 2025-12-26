from result import Err, Ok, Result

from infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository
from src.core.models.end_product_user import EndProductUser


class EndProductUserRepository(InMemoryRepository[EndProductUser]):
    def get_by_email(self, user_email: str) -> Result[EndProductUser, str]:
        matching_users = [u for u in self._storage.values() if u.user_email == user_email]

        if not matching_users:
            return Err(f"User with email '{user_email}' not found")

        return Ok(matching_users[0])

    def get_by_token(self, user_token: str) -> Result[EndProductUser, str]:
        matching_users = [u for u in self._storage.values() if u.user_token == user_token]

        if not matching_users:
            return Err("User with token not found")

        return Ok(matching_users[0])

    def get_by_email_case_insensitive(self, user_email: str) -> Result[EndProductUser, str]:
        matching_users = [u for u in self._storage.values() if u.user_email.lower() == user_email.lower()]

        if not matching_users:
            return Err(f"User with email '{user_email}' not found")

        return Ok(matching_users[0])
