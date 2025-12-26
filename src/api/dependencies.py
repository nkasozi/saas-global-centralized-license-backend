from fastapi import Depends

from src.core.models.activation import Activation
from src.core.models.audit_log import AuditLog
from src.core.models.brand import Brand
from src.core.models.end_product_user import EndProductUser
from src.core.models.licence import License
from src.core.models.licence_key import LicenseKey
from src.core.models.product import Product
from src.core.models.webhook import Webhook
from src.core.ports.auth_interface import AuthInterface
from src.core.ports.logger_interface import LoggerInterface
from src.core.ports.repository_interface import RepositoryInterface
from src.core.services.audit_service import AuditService
from src.core.services.brand_manager import BrandManager
from src.core.services.licence_manager import LicenseManager
from src.core.services.license_activation_service import LicenseActivationService
from src.core.services.license_provisioning_service import LicenseProvisioningService
from src.core.services.license_status_query_service import LicenseStatusQueryService
from src.core.services.product_manager import ProductManager
from src.core.services.user_manager import UserManager
from src.core.services.webhook_service import WebhookService
from src.infrastructure.auth.auth_service import AuthService
from src.infrastructure.logging.logger_adapter import LoggerAdapter
from src.infrastructure.persistence.file_based_db.activation_repository import ActivationRepository
from src.infrastructure.persistence.file_based_db.audit_log_repository import AuditLogRepository
from src.infrastructure.persistence.file_based_db.brand_repository import BrandRepository
from src.infrastructure.persistence.file_based_db.end_product_user_repository import EndProductUserRepository
from src.infrastructure.persistence.file_based_db.license_key_repository import LicenseKeyRepository
from src.infrastructure.persistence.file_based_db.license_repository import LicenseRepository
from src.infrastructure.persistence.file_based_db.product_repository import ProductRepository
from src.infrastructure.persistence.file_based_db.webhook_repository import WebhookRepository


def get_logger() -> LoggerInterface:
    return LoggerAdapter()


def get_brand_repository() -> RepositoryInterface[Brand]:
    return BrandRepository()


def get_product_repository() -> RepositoryInterface[Product]:
    return ProductRepository()


def get_license_repository() -> RepositoryInterface[License]:
    return LicenseRepository()


def get_license_key_repository() -> RepositoryInterface[LicenseKey]:
    return LicenseKeyRepository()


def get_activation_repository() -> RepositoryInterface[Activation]:
    return ActivationRepository()


def get_end_product_user_repository() -> RepositoryInterface[EndProductUser]:
    return EndProductUserRepository()


def get_audit_log_repository() -> RepositoryInterface[AuditLog]:
    return AuditLogRepository()


def get_webhook_repository() -> RepositoryInterface[Webhook]:
    return WebhookRepository()


def get_audit_service(
    audit_repository: RepositoryInterface[AuditLog] = Depends(get_audit_log_repository),
    logger: LoggerInterface = Depends(get_logger),
) -> AuditService:
    return AuditService(audit_repository, logger)


def get_webhook_service(
    webhook_repository: RepositoryInterface[Webhook] = Depends(get_webhook_repository),
    logger: LoggerInterface = Depends(get_logger),
) -> WebhookService:
    return WebhookService(webhook_repository, logger)


def get_brand_manager(
    repository: RepositoryInterface[Brand] = Depends(get_brand_repository),
    audit_service: AuditService = Depends(get_audit_service),
    logger: LoggerInterface = Depends(get_logger),
) -> BrandManager:
    return BrandManager(repository, audit_service, logger)


def get_product_manager(
    repository: RepositoryInterface[Product] = Depends(get_product_repository),
    audit_service: AuditService = Depends(get_audit_service),
    logger: LoggerInterface = Depends(get_logger),
) -> ProductManager:
    return ProductManager(repository, audit_service, logger)


def get_user_manager(
    repository: RepositoryInterface[EndProductUser] = Depends(get_end_product_user_repository),
    audit_service: AuditService = Depends(get_audit_service),
    logger: LoggerInterface = Depends(get_logger),
) -> UserManager:
    return UserManager(repository, audit_service, logger)


def get_license_manager(
    license_repository: RepositoryInterface[License] = Depends(get_license_repository),
    license_key_repository: RepositoryInterface[LicenseKey] = Depends(get_license_key_repository),
    end_product_user_repository: RepositoryInterface[EndProductUser] = Depends(get_end_product_user_repository),
    audit_service: AuditService = Depends(get_audit_service),
    logger: LoggerInterface = Depends(get_logger),
) -> LicenseManager:
    return LicenseManager(
        license_repository, license_key_repository, end_product_user_repository, audit_service, logger
    )


def get_license_provisioning_service(
    license_repository: RepositoryInterface[License] = Depends(get_license_repository),
    license_key_repository: RepositoryInterface[LicenseKey] = Depends(get_license_key_repository),
    product_repository: RepositoryInterface[Product] = Depends(get_product_repository),
    webhook_service: WebhookService = Depends(get_webhook_service),
    audit_service: AuditService = Depends(get_audit_service),
    logger: LoggerInterface = Depends(get_logger),
) -> LicenseProvisioningService:
    return LicenseProvisioningService(
        license_repository, license_key_repository, product_repository, webhook_service, audit_service, logger
    )


def get_license_activation_service(
    activation_repository: RepositoryInterface[Activation] = Depends(get_activation_repository),
    license_key_repository: RepositoryInterface[LicenseKey] = Depends(get_license_key_repository),
    license_repository: RepositoryInterface[License] = Depends(get_license_repository),
    product_repository: RepositoryInterface[Product] = Depends(get_product_repository),
    webhook_service: WebhookService = Depends(get_webhook_service),
    audit_service: AuditService = Depends(get_audit_service),
    logger: LoggerInterface = Depends(get_logger),
) -> LicenseActivationService:
    return LicenseActivationService(
        activation_repository,
        license_key_repository,
        license_repository,
        product_repository,
        webhook_service,
        audit_service,
        logger,
    )


def get_auth_service(
    brand_repository: RepositoryInterface[Brand] = Depends(get_brand_repository),
    license_key_repository: RepositoryInterface[LicenseKey] = Depends(get_license_key_repository),
    logger: LoggerInterface = Depends(get_logger),
) -> AuthInterface:
    return AuthService(brand_repository, license_key_repository, logger)


def get_license_status_query_service(
    license_key_repository: RepositoryInterface[LicenseKey] = Depends(get_license_key_repository),
    license_repository: RepositoryInterface[License] = Depends(get_license_repository),
    activation_repository: RepositoryInterface[Activation] = Depends(get_activation_repository),
    product_repository: RepositoryInterface[Product] = Depends(get_product_repository),
    logger: LoggerInterface = Depends(get_logger),
) -> LicenseStatusQueryService:
    return LicenseStatusQueryService(
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        logger,
    )
