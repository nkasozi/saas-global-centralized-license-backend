from src.core.models.audit_log import AuditLog
from src.infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository


class AuditLogRepository(InMemoryRepository[AuditLog]):
    pass
