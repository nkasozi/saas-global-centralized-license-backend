from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Ok

from src.core.models.audit_log import AuditLog, AuditOperation
from src.core.services.audit_service import AuditService


@pytest.fixture
def audit_repository() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def audit_service(audit_repository: Mock, logger: Mock) -> AuditService:
    return AuditService(audit_repository, logger)


@pytest.fixture
def test_audit_log() -> AuditLog:
    brand_id = str(uuid4())
    resource_id = str(uuid4())
    audit_result = AuditLog.create(
        brand_id=brand_id,
        operation=AuditOperation.LICENSE_PROVISIONED,
        resource_type="LICENSE",
        resource_id=resource_id,
        changes={"seats": 5},
        ip_address="192.168.1.1",
        user_agent="Chrome",
    )
    audit_log = audit_result.unwrap()
    return audit_log


class TestAuditService:
    def test_log_operation_success(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        resource_id = str(uuid4())
        audit_result = AuditLog.create(
            brand_id=brand_id,
            operation=AuditOperation.BRAND_CREATED,
            resource_type="BRAND",
            resource_id=resource_id,
        )
        audit_log = audit_result.unwrap()
        audit_repository.save.return_value = Ok(audit_log)

        result = audit_service.log_operation(
            brand_id=brand_id,
            operation=AuditOperation.BRAND_CREATED,
            resource_type="BRAND",
            resource_id=resource_id,
        )

        assert result.is_ok()
        audit_repository.save.assert_called_once()

    def test_log_operation_with_changes(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        resource_id = str(uuid4())
        changes = {"old_status": "ACTIVE", "new_status": "SUSPENDED"}
        audit_result = AuditLog.create(
            brand_id=brand_id,
            operation=AuditOperation.LICENSE_SUSPENDED,
            resource_type="LICENSE",
            resource_id=resource_id,
            changes=changes,
        )
        audit_log = audit_result.unwrap()
        audit_repository.save.return_value = Ok(audit_log)

        result = audit_service.log_operation(
            brand_id=brand_id,
            operation=AuditOperation.LICENSE_SUSPENDED,
            resource_type="LICENSE",
            resource_id=resource_id,
            changes=changes,
        )

        assert result.is_ok()
        saved_log = audit_repository.save.call_args[0][0]
        assert saved_log.changes == changes

    def test_log_failure_success(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        audit_result = AuditLog.create_failure(
            brand_id=brand_id,
            operation=AuditOperation.AUTH_FAILED,
            error_message="Invalid API key",
        )
        audit_log = audit_result.unwrap()
        audit_repository.save.return_value = Ok(audit_log)

        result = audit_service.log_failure(
            brand_id=brand_id,
            operation=AuditOperation.AUTH_FAILED,
            error_message="Invalid API key",
        )

        assert result.is_ok()
        assert result.unwrap().status == "FAILURE"
        audit_repository.save.assert_called_once()

    def test_get_brand_audit_logs_success(
        self, audit_service: AuditService, audit_repository: Mock, test_audit_log: AuditLog
    ) -> None:
        audit_repository.get_all.return_value = Ok([test_audit_log])

        result = audit_service.get_brand_audit_logs(brand_id=test_audit_log.brand_id)

        assert result.is_ok()
        logs = result.unwrap()
        assert len(logs) == 1
        assert logs[0].brand_id == test_audit_log.brand_id

    def test_get_brand_audit_logs_filters_by_brand(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id_1 = str(uuid4())
        brand_id_2 = str(uuid4())
        resource_id_1 = str(uuid4())
        resource_id_2 = str(uuid4())
        log1_result = AuditLog.create(brand_id_1, AuditOperation.BRAND_CREATED, "BRAND", resource_id_1)
        log2_result = AuditLog.create(brand_id_2, AuditOperation.BRAND_CREATED, "BRAND", resource_id_2)
        log1 = log1_result.unwrap()
        log2 = log2_result.unwrap()

        audit_repository.get_all.return_value = Ok([log1, log2])

        result = audit_service.get_brand_audit_logs(brand_id=brand_id_1)

        assert result.is_ok()
        logs = result.unwrap()
        assert len(logs) == 1
        assert logs[0].brand_id == brand_id_1

    def test_get_logs_by_operation_success(
        self, audit_service: AuditService, audit_repository: Mock, test_audit_log: AuditLog
    ) -> None:
        audit_repository.get_all.return_value = Ok([test_audit_log])

        result = audit_service.get_logs_by_operation(
            brand_id=test_audit_log.brand_id,
            operation=AuditOperation.LICENSE_PROVISIONED,
        )

        assert result.is_ok()
        logs = result.unwrap()
        assert all(log.operation == AuditOperation.LICENSE_PROVISIONED for log in logs)

    def test_get_logs_by_operation_filters_correctly(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        resource_id_1 = str(uuid4())
        resource_id_2 = str(uuid4())
        prov_result = AuditLog.create(brand_id, AuditOperation.LICENSE_PROVISIONED, "LICENSE", resource_id_1)
        activate_result = AuditLog.create(brand_id, AuditOperation.LICENSE_ACTIVATED, "LICENSE", resource_id_2)
        prov_log = prov_result.unwrap()
        activate_log = activate_result.unwrap()

        audit_repository.get_all.return_value = Ok([prov_log, activate_log])

        result = audit_service.get_logs_by_operation(
            brand_id=brand_id,
            operation=AuditOperation.LICENSE_PROVISIONED,
        )

        assert result.is_ok()
        logs = result.unwrap()
        assert len(logs) == 1
        assert logs[0].operation == AuditOperation.LICENSE_PROVISIONED

    def test_get_logs_by_resource_success(
        self, audit_service: AuditService, audit_repository: Mock, test_audit_log: AuditLog
    ) -> None:
        audit_repository.get_all.return_value = Ok([test_audit_log])

        result = audit_service.get_logs_by_resource(
            brand_id=test_audit_log.brand_id,
            resource_type="LICENSE",
            resource_id=test_audit_log.resource_id,
        )

        assert result.is_ok()
        logs = result.unwrap()
        assert all(log.resource_type == "LICENSE" for log in logs)
        assert all(log.resource_id == test_audit_log.resource_id for log in logs)

    def test_get_recent_failures_success(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        failure_result = AuditLog.create_failure(brand_id, AuditOperation.AUTH_FAILED, "Invalid key")
        failure_log = failure_result.unwrap()

        audit_repository.get_all.return_value = Ok([failure_log])

        result = audit_service.get_recent_failures(brand_id=brand_id, hours=24)

        assert result.is_ok()
        logs = result.unwrap()
        assert all(log.status == "FAILURE" for log in logs)

    def test_get_recent_failures_filters_by_time(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        failure_result = AuditLog.create_failure(brand_id, AuditOperation.AUTH_FAILED, "Invalid key")
        failure_log = failure_result.unwrap()
        failure_log.timestamp = datetime.now(timezone.utc)

        audit_repository.get_all.return_value = Ok([failure_log])

        result = audit_service.get_recent_failures(brand_id=brand_id, hours=1)

        assert result.is_ok()
        logs = result.unwrap()
        assert len(logs) == 1

    def test_log_operation_invalid_brand_id(self, audit_service: AuditService) -> None:
        result = audit_service.log_operation(
            brand_id="",
            operation=AuditOperation.BRAND_CREATED,
            resource_type="BRAND",
            resource_id=str(uuid4()),
        )

        assert result.is_err()

    def test_log_operation_missing_resource_type(self, audit_service: AuditService) -> None:
        result = audit_service.log_operation(
            brand_id=str(uuid4()),
            operation=AuditOperation.BRAND_CREATED,
            resource_type="",
            resource_id=str(uuid4()),
        )

        assert result.is_err()

    def test_audit_logs_sorted_by_timestamp(self, audit_service: AuditService, audit_repository: Mock) -> None:
        brand_id = str(uuid4())
        resource_id_1 = str(uuid4())
        resource_id_2 = str(uuid4())
        log1_result = AuditLog.create(brand_id, AuditOperation.BRAND_CREATED, "BRAND", resource_id_1)
        log2_result = AuditLog.create(brand_id, AuditOperation.BRAND_CREATED, "BRAND", resource_id_2)
        log1 = log1_result.unwrap()
        log2 = log2_result.unwrap()
        log1.timestamp = datetime(2025, 1, 1)
        log2.timestamp = datetime(2025, 1, 2)

        audit_repository.get_all.return_value = Ok([log1, log2])

        result = audit_service.get_brand_audit_logs(brand_id=brand_id)

        assert result.is_ok()
        logs = result.unwrap()
        assert logs[0].timestamp >= logs[1].timestamp
