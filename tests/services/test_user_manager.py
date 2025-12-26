from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.end_product_user import EndProductUser
from src.core.services.user_manager import UserManager


@pytest.fixture
def user_repository() -> Mock:
    return Mock()


@pytest.fixture
def brand_repository() -> Mock:
    return Mock()


@pytest.fixture
def audit_service() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def user_manager(user_repository: Mock, audit_service: Mock, logger: Mock) -> UserManager:
    return UserManager(user_repository, audit_service, logger)


@pytest.fixture
def test_user() -> EndProductUser:
    user_result = EndProductUser.create("john@example.com", "token-123")
    return user_result.unwrap()


class TestUserManager:
    def test_create_user_success(self, user_manager: UserManager, user_repository: Mock) -> None:
        user_result = EndProductUser.create("test@example.com", "token-abc")
        user = user_result.unwrap()
        user_repository.save.return_value = Ok(user)

        result = user_manager.create_user("test@example.com", "token-abc")

        assert result.is_ok()
        created = result.unwrap()
        assert created.user_email == "test@example.com"
        assert created.user_token == "token-abc"
        assert isinstance(created.id, str)
        user_repository.save.assert_called_once()

    def test_create_user_invalid_email_empty(self, user_manager: UserManager) -> None:
        result = user_manager.create_user("", "token-123")

        assert result.is_err()
        assert "Email" in result.unwrap_err()

    def test_create_user_invalid_email_format(self, user_manager: UserManager) -> None:
        result = user_manager.create_user("invalid-email", "token-123")

        assert result.is_err()
        assert "Email" in result.unwrap_err()

    def test_create_user_invalid_email_no_domain(self, user_manager: UserManager) -> None:
        result = user_manager.create_user("user@invalid", "token-123")

        assert result.is_err()

    def test_create_user_invalid_token_empty(self, user_manager: UserManager) -> None:
        result = user_manager.create_user("test@example.com", "")

        assert result.is_err()
        assert "token" in result.unwrap_err().lower()

    def test_create_user_invalid_token_whitespace(self, user_manager: UserManager) -> None:
        result = user_manager.create_user("test@example.com", "   ")

        assert result.is_err()

    def test_get_user_by_id_success(
        self, user_manager: UserManager, user_repository: Mock, test_user: EndProductUser
    ) -> None:
        user_id = str(uuid4())
        test_user.id = user_id
        user_repository.get_by_id.return_value = Ok(test_user)

        result = user_manager.get_user_by_id(user_id)

        assert result.is_ok()
        assert result.unwrap().id == user_id
        user_repository.get_by_id.assert_called_once_with(user_id)

    def test_get_user_by_id_not_found(self, user_manager: UserManager, user_repository: Mock) -> None:
        user_id = str(uuid4())
        user_repository.get_by_id.return_value = Err(f"Entity with id {user_id} not found")

        result = user_manager.get_user_by_id(user_id)

        assert result.is_err()

    def test_get_user_by_email_success(
        self, user_manager: UserManager, user_repository: Mock, test_user: EndProductUser
    ) -> None:
        test_user.user_email = "john@example.com"
        user_repository.get_all.return_value = Ok([test_user])

        result = user_manager.get_user_by_email("john@example.com")

        assert result.is_ok()
        retrieved_user = result.unwrap()
        assert retrieved_user.user_email == "john@example.com"
        user_repository.get_all.assert_called_once()

    def test_get_user_by_email_not_found(self, user_manager: UserManager, user_repository: Mock) -> None:
        user_repository.get_by_email.return_value = Err("User not found")

        result = user_manager.get_user_by_email("notfound@example.com")

        assert result.is_err()

    def test_get_all_users_success(self, user_manager: UserManager, user_repository: Mock) -> None:
        user1_result = EndProductUser.create("user1@example.com", "token1")
        user2_result = EndProductUser.create("user2@example.com", "token2")
        users = [user1_result.unwrap(), user2_result.unwrap()]
        user_repository.get_all.return_value = Ok(users)

        result = user_manager.get_all_users()

        assert result.is_ok()
        all_users = result.unwrap()
        assert len(all_users) == 2
        assert all(isinstance(u.id, str) for u in all_users)
        user_repository.get_all.assert_called_once()

    def test_get_all_users_empty(self, user_manager: UserManager, user_repository: Mock) -> None:
        user_repository.get_all.return_value = Ok([])

        result = user_manager.get_all_users()

        assert result.is_ok()
        assert result.unwrap() == []

    def test_get_user_by_email_case_insensitive(
        self, user_manager: UserManager, user_repository: Mock, test_user: EndProductUser
    ) -> None:
        test_user.id = "1"
        test_user.user_email = "john@example.com"
        user_repository.get_all.return_value = Ok([test_user])

        result = user_manager.get_user_by_email("JOHN@EXAMPLE.COM")

        assert result.is_ok()
        assert result.unwrap().user_email == "john@example.com"

    def test_user_manager_creates_unique_users(self, user_manager: UserManager, user_repository: Mock) -> None:
        user1_result = EndProductUser.create("user1@example.com", "User 1")
        user2_result = EndProductUser.create("user2@example.com", "User 2")
        user1 = user1_result.unwrap()
        user2 = user2_result.unwrap()

        user_repository.save.side_effect = [Ok(user1), Ok(user2)]

        result1 = user_manager.create_user("user1@example.com", "User 1")
        result2 = user_manager.create_user("user2@example.com", "User 2")

        assert result1.is_ok()
        assert result2.is_ok()
        id1 = result1.unwrap().id
        id2 = result2.unwrap().id
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
