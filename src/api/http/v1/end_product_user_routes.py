from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.api.auth_helpers import get_license_key_from_request
from src.api.dependencies import get_license_activation_service, get_license_status_query_service
from src.core.models.activation import InstanceIDType
from src.core.services.license_activation_service import LicenseActivationService
from src.core.services.license_status_query_service import LicenseStatusQueryService

router = APIRouter()


class InstanceIDTypeEnum(str, Enum):
    URL = "url"
    HOST = "host"
    MACHINE_ID = "machine_id"


class ActivateLicenseRequest(BaseModel):
    instance_id_type: InstanceIDTypeEnum
    instance_id: str


class ActivateLicenseResponse(BaseModel):
    activation_id: str
    license_key: str
    instance_id: str
    activated_at: datetime


class CheckStatusRequest(BaseModel):
    pass


class LicenseData(BaseModel):
    license_id: str
    product_id: str
    product_name: str
    status: str
    expires_at: str
    is_active: bool


class ActivationData(BaseModel):
    activation_id: str
    instance_id: str
    instance_id_type: str
    activated_at: str


class CheckStatusResponse(BaseModel):
    license_key_id: str
    key_string: str
    created_at: str
    is_valid: bool
    licenses: list[LicenseData]
    activations: list[ActivationData]


class DeactivateRequest(BaseModel):
    activation_id: str


class DeactivateResponse(BaseModel):
    activation_id: str
    message: str


@router.post(
    "/license/activate",
    response_model=ActivateLicenseResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={
        "parameters": [
            {
                "name": "X-LICENSE-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "License key for license authentication",
            }
        ]
    },
)
async def activate_license(
    request_body: ActivateLicenseRequest,
    request: Request,
    activation_service: LicenseActivationService = Depends(get_license_activation_service),
) -> ActivateLicenseResponse:
    license_key = get_license_key_from_request(request)
    instance_id_type = InstanceIDType(request_body.instance_id_type.value)
    ip_address = request.client.host if request.client else "unknown"

    activation_result = activation_service.activate_license_for_instance(
        license_key_string=license_key,
        instance_id_type=instance_id_type,
        instance_id=request_body.instance_id,
        ip_address=ip_address,
    )

    if activation_result.is_err():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=activation_result.err_value)

    activation = activation_result.ok_value
    return ActivateLicenseResponse(
        activation_id=activation.id,
        license_key=license_key,
        instance_id=activation.instance_id,
        activated_at=activation.activated_at,
    )


@router.post(
    "/license/check-status",
    response_model=CheckStatusResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-LICENSE-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "License key for license authentication",
            }
        ]
    },
)
async def check_license_status(
    request: Request, query_service: LicenseStatusQueryService = Depends(get_license_status_query_service)
) -> CheckStatusResponse:
    license_key = get_license_key_from_request(request)
    status_result = query_service.get_license_key_status(license_key)

    if status_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=status_result.err_value)

    return status_result.ok_value


@router.post(
    "/license/deactivate",
    response_model=DeactivateResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "X-LICENSE-KEY",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "License key for license authentication",
            }
        ]
    },
)
async def deactivate_instance(
    request_body: DeactivateRequest,
    request: Request,
    activation_service: LicenseActivationService = Depends(get_license_activation_service),
) -> DeactivateResponse:
    _ = get_license_key_from_request(request)

    deactivate_result = activation_service.deactivate_instance(request_body.activation_id)

    if deactivate_result.is_err():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=deactivate_result.err_value)

    return DeactivateResponse(activation_id=request_body.activation_id, message="Instance deactivated successfully")
