from fastapi import HTTPException, Request


def get_brand_api_key_from_request(request: Request) -> str:
    if not hasattr(request.state, "api_key"):
        raise HTTPException(status_code=401, detail="Brand API Key not found in request")

    return request.state.api_key


def get_license_key_from_request(request: Request) -> str:
    if not hasattr(request.state, "license_key"):
        raise HTTPException(status_code=401, detail="License key not found in request")

    return request.state.license_key
