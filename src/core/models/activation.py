from datetime import datetime
from enum import Enum

from src.core.models.model import Model


class InstanceIDType(Enum):
    URL = "url"
    Host = "Host"
    MachineID = "MachineID"

class Activation (Model):
    id: int
    license_key_id: int
    instance_id_type: InstanceIDType
    instance_id: str
    ip_address: str
    activated_at: datetime