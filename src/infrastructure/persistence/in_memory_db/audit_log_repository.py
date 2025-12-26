from infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository
from src.core.models.audit_log import AuditLog


class AuditLogRepository(InMemoryRepository[AuditLog]):
    pass
