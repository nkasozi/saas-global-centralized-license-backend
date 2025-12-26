from datetime import datetime, timezone

from result import Err, Result

from src.core.models.audit_log import AuditOperation
from src.core.models.end_product_user import EndProductUser
from src.core.models.licence import License, LicenseStatus
from src.core.models.licence_key import LicenseKey
from src.core.ports.logger_interface import LoggerInterface
from src.core.ports.repository_interface import RepositoryInterface
from src.core.services.manager_interface import Manager


class LicenseManager(Manager):
    def __init__(
        self,
        license_repository: RepositoryInterface[License],
        license_key_repository: RepositoryInterface[LicenseKey],
        end_product_user_repository: RepositoryInterface[EndProductUser],
        audit_service,
        logger: LoggerInterface,
    ):
        self.license_repository = license_repository
        self.license_key_repository = license_key_repository
        self.end_product_user_repository = end_product_user_repository
        self.audit_service = audit_service
        self.logger = logger

    def create_license(self, product_id: str, expires_at: datetime) -> Result[License, str]:
        license_creation_result = License.create(product_id, expires_at)

        if license_creation_result.is_err():
            self.logger.error(f"License creation failed: {license_creation_result.err_value}")
            return license_creation_result

        license_obj = license_creation_result.ok_value
        return self.license_repository.save(license_obj)

    def get_license_by_id(self, license_id: str) -> Result[License, str]:
        return self.license_repository.get_by_id(license_id)

    def suspend_license(self, license_id: str, brand_id: str | None = None) -> Result[License, str]:
        license_result = self.license_repository.get_by_id(license_id)

        if license_result.is_err():
            return license_result

        license_obj = license_result.ok_value
        license_obj.status = LicenseStatus.SUSPENDED
        saved_result = self.license_repository.save(license_obj)

        if saved_result.is_ok() and brand_id:
            self.audit_service.log_operation(
                brand_id=brand_id,
                operation=AuditOperation.LICENSE_SUSPENDED,
                resource_id=license_id,
                resource_type="license",
                changes={"status": LicenseStatus.SUSPENDED.value},
            )

        return saved_result

    def resume_license(self, license_id: str, brand_id: str | None = None) -> Result[License, str]:
        license_result = self.license_repository.get_by_id(license_id)

        if license_result.is_err():
            return license_result

        license_obj = license_result.ok_value
        license_obj.status = LicenseStatus.VALID
        saved_result = self.license_repository.save(license_obj)

        if saved_result.is_ok() and brand_id:
            self.audit_service.log_operation(
                brand_id=brand_id,
                operation=AuditOperation.LICENSE_RESUMED,
                resource_id=license_id,
                resource_type="license",
                changes={"status": LicenseStatus.VALID.value},
            )

        return saved_result

    def cancel_license(self, license_id: str, brand_id: str | None = None) -> Result[License, str]:
        license_result = self.license_repository.get_by_id(license_id)

        if license_result.is_err():
            return license_result

        license_obj = license_result.ok_value
        license_obj.status = LicenseStatus.CANCELLED
        saved_result = self.license_repository.save(license_obj)

        if saved_result.is_ok() and brand_id:
            self.audit_service.log_operation(
                brand_id=brand_id,
                operation=AuditOperation.LICENSE_CANCELLED,
                resource_id=license_id,
                resource_type="license",
                changes={"status": LicenseStatus.CANCELLED.value},
            )

        return saved_result

    def renew_license(
        self, license_id: str, new_expiration_date: datetime, brand_id: str | None = None
    ) -> Result[License, str]:
        license_result = self.license_repository.get_by_id(license_id)

        if license_result.is_err():
            return license_result

        if new_expiration_date <= datetime.now(timezone.utc):
            return Err("New expiration date must be in the future")

        license_obj = license_result.ok_value
        license_obj.expires_at = new_expiration_date
        saved_result = self.license_repository.save(license_obj)

        if saved_result.is_ok() and brand_id:
            self.audit_service.log_operation(
                brand_id=brand_id,
                operation=AuditOperation.LICENSE_RENEWED,
                resource_id=license_id,
                resource_type="license",
                changes={"expires_at": new_expiration_date.isoformat()},
            )

        return saved_result
