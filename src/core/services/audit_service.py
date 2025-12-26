from datetime import datetime, timezone
from typing import Optional

from result import Ok, Result

from src.core.models.audit_log import AuditLog, AuditOperation
from src.core.ports.logger_interface import LoggerInterface
from src.core.ports.repository_interface import RepositoryInterface


class AuditService:
    def __init__(
        self,
        audit_repository: RepositoryInterface[AuditLog],
        logger: LoggerInterface,
    ):
        self.audit_repository = audit_repository
        self.logger = logger

    def log_operation(
        self,
        brand_id: str,
        operation: AuditOperation,
        resource_type: str,
        resource_id: str,
        changes: Optional[dict] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Result[AuditLog, str]:
        audit_log_result = AuditLog.create(
            brand_id=brand_id,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if audit_log_result.is_err():
            self.logger.error(f"Failed to create audit log: {audit_log_result.unwrap_err()}")
            return audit_log_result

        audit_log = audit_log_result.unwrap()
        save_result = self.audit_repository.save(audit_log)

        if save_result.is_err():
            self.logger.error(f"Failed to save audit log: {save_result.unwrap_err()}")
            return save_result

        self.logger.debug(f"Audit logged: {operation.value} for {resource_type} {resource_id}")
        return Ok(save_result.unwrap())

    def log_failure(
        self,
        brand_id: str,
        operation: AuditOperation,
        error_message: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Result[AuditLog, str]:
        audit_log_result = AuditLog.create_failure(
            brand_id=brand_id,
            operation=operation,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if audit_log_result.is_err():
            self.logger.error(f"Failed to create failure audit log: {audit_log_result.unwrap_err()}")
            return audit_log_result

        audit_log = audit_log_result.unwrap()
        save_result = self.audit_repository.save(audit_log)

        if save_result.is_err():
            self.logger.error(f"Failed to save failure audit log: {save_result.unwrap_err()}")
            return save_result

        self.logger.warning(f"Operation failed: {operation.value} - {error_message}")
        return Ok(save_result.unwrap())

    def get_brand_audit_logs(
        self,
        brand_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[list[AuditLog], str]:
        all_logs_result = self.audit_repository.get_all()

        if all_logs_result.is_err():
            return all_logs_result

        all_logs = all_logs_result.unwrap()
        brand_logs = [log for log in all_logs if log.brand_id == brand_id]
        brand_logs.sort(key=lambda x: x.timestamp, reverse=True)

        paginated_logs = brand_logs[offset : offset + limit]
        self.logger.debug(f"Retrieved {len(paginated_logs)} audit logs for brand {brand_id}")
        return Ok(paginated_logs)

    def get_logs_by_operation(
        self,
        brand_id: str,
        operation: AuditOperation,
        limit: int = 50,
    ) -> Result[list[AuditLog], str]:
        all_logs_result = self.audit_repository.get_all()

        if all_logs_result.is_err():
            return all_logs_result

        all_logs = all_logs_result.unwrap()
        filtered_logs = [log for log in all_logs if log.brand_id == brand_id and log.operation == operation]
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        limited_logs = filtered_logs[:limit]
        self.logger.debug(f"Retrieved {len(limited_logs)} {operation.value} logs for brand {brand_id}")
        return Ok(limited_logs)

    def get_logs_by_resource(
        self,
        brand_id: str,
        resource_type: str,
        resource_id: str,
    ) -> Result[list[AuditLog], str]:
        all_logs_result = self.audit_repository.get_all()

        if all_logs_result.is_err():
            return all_logs_result

        all_logs = all_logs_result.unwrap()
        filtered_logs = [
            log
            for log in all_logs
            if (log.brand_id == brand_id and log.resource_type == resource_type and log.resource_id == resource_id)
        ]
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        self.logger.debug(f"Retrieved {len(filtered_logs)} logs for {resource_type} {resource_id}")
        return Ok(filtered_logs)

    def get_recent_failures(
        self,
        brand_id: str,
        hours: int = 24,
    ) -> Result[list[AuditLog], str]:
        all_logs_result = self.audit_repository.get_all()

        if all_logs_result.is_err():
            return all_logs_result

        all_logs = all_logs_result.unwrap()
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        failure_logs = [
            log
            for log in all_logs
            if (log.brand_id == brand_id and log.status == "FAILURE" and log.timestamp.timestamp() > cutoff_time)
        ]
        failure_logs.sort(key=lambda x: x.timestamp, reverse=True)

        self.logger.debug(f"Retrieved {len(failure_logs)} failure logs from last {hours} hours for brand {brand_id}")
        return Ok(failure_logs)
