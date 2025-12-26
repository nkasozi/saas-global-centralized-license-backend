from src.core.models.audit_log import AuditLog
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class AuditLogRepository(FileRepository[AuditLog]):
    def __init__(self):
        super().__init__("data/audit_logs.json", AuditLog)
