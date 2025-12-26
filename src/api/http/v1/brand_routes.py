from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.api.auth_helpers import get_brand_api_key_from_request
from src.api.dependencies import (
    get_auth_service,
    get_brand_manager,
    get_license_manager,
    get_license_provisioning_service,
    get_license_status_query_service,
    get_product_manager,
    get_user_manager,
)
from src.core.ports.auth_interface import AuthInterface
from src.core.services.brand_manager import BrandManager
from src.core.services.licence_manager import LicenseManager
from src.core.services.license_provisioning_service import LicenseProvisioningService
from src.core.services.license_status_query_service import LicenseStatusQueryService
from src.core.services.product_manager import ProductManager
from src.core.services.user_manager import UserManager

router = APIRouter()


class CreateBrandRequest(BaseModel):
    brand_name: str


class CreateBrandResponse(BaseModel):
    brand_id: str
    brand_name: str
    api_key: str


class ProvisionLicenseRequest(BaseModel):
    product_id: str
    end_product_user_email: str
    expiration_date: datetime


class ProvisionLicenseResponse(BaseModel):
    license_id: str
    license_key: str
    product_id: str
    status: str


class LicenseLifecycleRequest(BaseModel):
    new_expiration_date: datetime | None = None


class CreateProductRequest(BaseModel):
    product_name: str
    max_seats: int


class ProductResponse(BaseModel):
    product_id: str
    brand_id: str
    product_name: str
    max_seats: int
    created_at: str


class UpdateProductRequest(BaseModel):
    product_name: str | None = None
    max_seats: int | None = None


class ListProductsResponse(BaseModel):
    brand_id: str
    products: list[ProductResponse]


class LicenseKeyStatusData(BaseModel):
    license_key_id: str
    key_string: str
    created_at: str
    is_valid: bool
    licenses: list
    activations: list


class ListCustomerLicensesResponse(BaseModel):
    customer_email: str | None
    licenses: list[LicenseKeyStatusData]


class SuspendLicenseResponse(BaseModel):
    license_id: str
    status: str
    message: str


class ResumeLicenseResponse(BaseModel):
    license_id: str
    status: str
    message: str


class RenewLicenseResponse(BaseModel):
    license_id: str
    expires_at: str
    message: str


class CancelLicenseResponse(BaseModel):
    license_id: str
    status: str
    message: str


class CreateWebhookRequest(BaseModel):
    url: str
    events: list[str]
    secret: str = Field(..., min_length=8)


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    status: str
    created_at: str
    updated_at: str
    last_triggered_at: str | None = None
    failure_count: int


class ListWebhooksResponse(BaseModel):
    webhooks: list[WebhookResponse]


class UpdateWebhookRequest(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    secret: str | None = Field(None, min_length=8)


class DeleteWebhookResponse(BaseModel):
    message: str


@router.post("", response_model=CreateBrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    request: CreateBrandRequest, brand_manager: BrandManager = Depends(get_brand_manager)
) -> CreateBrandResponse:
    creation_result = brand_manager.create_brand(request.brand_name)

    if creation_result.is_err():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=creation_result.err_value)

    created_brand = creation_result.ok_value
    return CreateBrandResponse(
        brand_id=created_brand.id, brand_name=created_brand.brand_name, api_key=created_brand.api_hash_key
    )


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def create_product(
    request_body: CreateProductRequest,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> ProductResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    creation_result = product_manager.create_product(
        brand_result.ok_value.id, request_body.product_name, request_body.max_seats
    )

    if creation_result.is_err():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=creation_result.err_value)

    created_product = creation_result.ok_value
    return ProductResponse(
        product_id=created_product.id,
        brand_id=created_product.brand_id,
        product_name=created_product.product_name,
        max_seats=created_product.max_seats,
        created_at=created_product.created_at.isoformat(),
    )


@router.get(
    "/products",
    response_model=ListProductsResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def list_brand_products(
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> ListProductsResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    products_result = product_manager.get_products_by_brand_id(brand_result.ok_value.id)

    if products_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=products_result.err_value)

    products = products_result.ok_value
    return ListProductsResponse(
        brand_id=brand_result.ok_value.id,
        products=[
            ProductResponse(
                product_id=p.id,
                brand_id=p.brand_id,
                product_name=p.product_name,
                max_seats=p.max_seats,
                created_at=p.created_at.isoformat(),
            )
            for p in products
        ],
    )


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def update_product(
    product_id: str,
    request_body: UpdateProductRequest,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> ProductResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    product_result = product_manager.get_product_by_id(product_id)

    if product_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=product_result.err_value)

    if product_result.ok_value.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Product does not belong to this brand")

    update_result = product_manager.update_product(product_id, request_body.product_name, request_body.max_seats)

    if update_result.is_err():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=update_result.err_value)

    updated_product = update_result.ok_value
    return ProductResponse(
        product_id=updated_product.id,
        brand_id=updated_product.brand_id,
        product_name=updated_product.product_name,
        max_seats=updated_product.max_seats,
        created_at=updated_product.created_at.isoformat(),
    )


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def delete_product(
    product_id: str,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> None:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    product_result = product_manager.get_product_by_id(product_id)

    if product_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=product_result.err_value)

    if product_result.ok_value.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Product does not belong to this brand")

    delete_result = product_manager.delete_product(product_id)

    if delete_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=delete_result.err_value)


@router.get(
    "/licenses",
    response_model=ListCustomerLicensesResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def list_customer_licenses(
    customer_email: str | None = None,
    request: Request = None,
    brand_manager: BrandManager = Depends(get_brand_manager),
    query_service: LicenseStatusQueryService = Depends(get_license_status_query_service),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> ListCustomerLicensesResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    if customer_email:
        licenses_result = query_service.get_licenses_by_customer_email(customer_email, brand_result.ok_value.id)
    else:
        licenses_result = query_service.get_all_brand_licenses(brand_result.ok_value.id)

    if licenses_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=licenses_result.err_value)

    return ListCustomerLicensesResponse(customer_email=customer_email, licenses=licenses_result.ok_value)


@router.post(
    "/licenses/provision",
    response_model=ProvisionLicenseResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def provision_license(
    request_body: ProvisionLicenseRequest,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    provisioning_service: LicenseProvisioningService = Depends(get_license_provisioning_service),
    user_manager: UserManager = Depends(get_user_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> ProvisionLicenseResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    product_result = product_manager.get_product_by_id(request_body.product_id)
    if product_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product = product_result.ok_value
    if product.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Product does not belong to this brand")

    if request_body.expiration_date <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expiration date must be in the future")

    user_result = user_manager.get_user_by_email(request_body.end_product_user_email)

    end_product_user_id: str
    if user_result.is_err():
        import uuid

        create_user_result = user_manager.create_user(request_body.end_product_user_email, str(uuid.uuid4()))
        if create_user_result.is_err():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=create_user_result.err_value)
        end_product_user_id = create_user_result.ok_value.id
    else:
        end_product_user_id = user_result.ok_value.id

    provision_result = provisioning_service.provision_license_for_product(
        product_id=request_body.product_id,
        brand_id=brand_result.ok_value.id,
        end_product_user_id=end_product_user_id,
        expiration_date=request_body.expiration_date,
    )

    if provision_result.is_err():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=provision_result.err_value)

    license_obj, license_key = provision_result.ok_value
    return ProvisionLicenseResponse(
        license_id=license_obj.id,
        license_key=license_key.key_string,
        product_id=license_obj.product_id,
        status=license_obj.status.value,
    )


@router.put(
    "/licenses/{license_id}/suspend",
    response_model=SuspendLicenseResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def suspend_license(
    license_id: str,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    license_manager: LicenseManager = Depends(get_license_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> SuspendLicenseResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    license_result = license_manager.get_license_by_id(license_id)
    if license_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    license_obj = license_result.ok_value
    product_result = product_manager.get_product_by_id(license_obj.product_id)
    if product_result.is_err() or product_result.ok_value.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License does not belong to this brand")

    suspend_result = license_manager.suspend_license(license_id)

    if suspend_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=suspend_result.err_value)

    suspended_license = suspend_result.ok_value
    return SuspendLicenseResponse(
        license_id=suspended_license.id, status=suspended_license.status.value, message="License suspended successfully"
    )


@router.put(
    "/licenses/{license_id}/resume",
    response_model=ResumeLicenseResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def resume_license(
    license_id: str,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    license_manager: LicenseManager = Depends(get_license_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> ResumeLicenseResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    license_result = license_manager.get_license_by_id(license_id)
    if license_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    license_obj = license_result.ok_value
    product_result = product_manager.get_product_by_id(license_obj.product_id)
    if product_result.is_err() or product_result.ok_value.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License does not belong to this brand")

    resume_result = license_manager.resume_license(license_id)

    if resume_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resume_result.err_value)

    resumed_license = resume_result.ok_value
    return ResumeLicenseResponse(
        license_id=resumed_license.id, status=resumed_license.status.value, message="License resumed successfully"
    )


@router.put(
    "/licenses/{license_id}/renew",
    response_model=RenewLicenseResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def renew_license(
    license_id: str,
    request_body: LicenseLifecycleRequest,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    license_manager: LicenseManager = Depends(get_license_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> RenewLicenseResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    if request_body.new_expiration_date <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="new_expiration_date must be in the future")

    license_result = license_manager.get_license_by_id(license_id)
    if license_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    license_obj = license_result.ok_value
    product_result = product_manager.get_product_by_id(license_obj.product_id)
    if product_result.is_err() or product_result.ok_value.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License does not belong to this brand")

    renew_result = license_manager.renew_license(license_id, request_body.new_expiration_date)

    if renew_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=renew_result.err_value)

    renewed_license = renew_result.ok_value
    return RenewLicenseResponse(
        license_id=renewed_license.id,
        expires_at=renewed_license.expires_at.isoformat(),
        message="License renewed successfully",
    )


@router.delete(
    "/licenses/{license_id}",
    response_model=CancelLicenseResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-API-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key for brand authentication",
            }
        ]
    },
)
async def cancel_license(
    license_id: str,
    request: Request,
    brand_manager: BrandManager = Depends(get_brand_manager),
    license_manager: LicenseManager = Depends(get_license_manager),
    product_manager: ProductManager = Depends(get_product_manager),
    auth_service: AuthInterface = Depends(get_auth_service),
) -> CancelLicenseResponse:
    brand_api_key = get_brand_api_key_from_request(request)

    brand_result = brand_manager.get_brand_by_api_key(brand_api_key)
    if brand_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    license_result = license_manager.get_license_by_id(license_id)
    if license_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    license_obj = license_result.ok_value
    product_result = product_manager.get_product_by_id(license_obj.product_id)
    if product_result.is_err() or product_result.ok_value.brand_id != brand_result.ok_value.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License does not belong to this brand")

    cancel_result = license_manager.cancel_license(license_id)

    if cancel_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=cancel_result.err_value)

    cancelled_license = cancel_result.ok_value
    return CancelLicenseResponse(
        license_id=cancelled_license.id, status=cancelled_license.status.value, message="License cancelled successfully"
    )

    return DeleteWebhookResponse(message="Webhook deleted successfully")
