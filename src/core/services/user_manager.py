from typing import List

from result import Err, Ok, Result

from src.core.models.audit_log import AuditOperation
from src.core.models.end_product_user import EndProductUser
from src.core.ports.logger_interface import LoggerInterface
from src.core.ports.repository_interface import RepositoryInterface
from src.core.services.manager_interface import Manager


class UserManager(Manager):
    def __init__(
        self,
        user_repository: RepositoryInterface[EndProductUser],
        audit_service,
        logger: LoggerInterface,
    ):
        self.user_repository = user_repository
        self.audit_service = audit_service
        self.logger = logger

    def create_user(self, user_email: str, user_token: str) -> Result[EndProductUser, str]:
        user_creation_result = EndProductUser.create(user_email, user_token)

        if user_creation_result.is_err():
            self.logger.error(f"User creation failed: {user_creation_result.err_value}")
            return user_creation_result

        user = user_creation_result.ok_value
        saved_user_result = self.user_repository.save(user)

        if saved_user_result.is_ok():
            saved_user = saved_user_result.ok_value
            self.audit_service.log_operation(
                brand_id="system",
                operation=AuditOperation.USER_CREATED,
                resource_id=saved_user.id,
                resource_type="user",
                changes={"email": saved_user.user_email},
            )

        return saved_user_result

    def get_user_by_id(self, user_id: str) -> Result[EndProductUser, str]:
        return self.user_repository.get_by_id(user_id)

    def get_user_by_email(self, user_email: str) -> Result[EndProductUser, str]:
        all_users_result = self.user_repository.get_all()
        if all_users_result.is_err():
            return all_users_result
        all_users = all_users_result.ok_value
        matching_users = [user for user in all_users if user.user_email.lower() == user_email.lower()]
        if not matching_users:
            return Err("User not found")
        return Ok(matching_users[0])

    def get_all_users(self) -> Result[List[EndProductUser], str]:
        return self.user_repository.get_all()
