from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from result import Err, Ok, Result

from src.core.models.model import Model


class InstanceIDType(Enum):
    URL = "url"
    HOST = "host"
    MACHINE_ID = "machine_id"


@dataclass
class Activation(Model):
    license_key_id: str = ""
    instance_id_type: InstanceIDType = InstanceIDType.URL
    instance_id: str = ""
    ip_address: str = ""
    activated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(
        license_key_id: str, instance_id_type: InstanceIDType, instance_id: str, ip_address: str
    ) -> Result["Activation", str]:
        if not license_key_id or not license_key_id.strip():
            return Err("License key ID cannot be empty")
        if not instance_id or not instance_id.strip():
            return Err("Instance ID cannot be empty")
        if not ip_address or not ip_address.strip():
            return Err("IP address cannot be empty")
        return Ok(
            Activation(
                id=str(uuid4()),
                license_key_id=license_key_id,
                instance_id_type=instance_id_type,
                instance_id=instance_id,
                ip_address=ip_address,
                activated_at=datetime.now(timezone.utc),
            )
        )
