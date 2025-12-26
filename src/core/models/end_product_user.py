import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from result import Err, Ok, Result

from src.core.models.model import Model


@dataclass
class EndProductUser(Model):
    user_email: str = ""
    user_token: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(user_email: str, user_token: str) -> Result["EndProductUser", str]:
        email_validation_error = EndProductUser._validate_email(user_email)
        if email_validation_error:
            return email_validation_error

        if not user_token or not user_token.strip():
            return Err("User token cannot be empty")

        return Ok(
            EndProductUser(
                id=str(uuid4()), user_email=user_email, user_token=user_token, created_at=datetime.now(timezone.utc)
            )
        )

    @staticmethod
    def _validate_email(email: str) -> Result[None, str] | None:
        if not email or not email.strip():
            return Err("Email cannot be empty")
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return Err("Email format is invalid")
        return None
