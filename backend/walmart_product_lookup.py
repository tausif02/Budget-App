import base64
import json
import os
import re
import time
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import (
    hashes,
    serialization,
)
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv


load_dotenv()


PRODUCT_LOOKUP_PATH = (
    "/api-proxy/service/affil/product/v2/items"
)

UPC_PATTERN = re.compile(r"^\d{12}$")


def get_required_setting(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required environment setting: {name}"
        )

    return value.strip()


def load_walmart_private_key():
    private_key_path = Path(
        get_required_setting(
            "WALMART_PRIVATE_KEY_PATH"
        )
    ).expanduser()

    if not private_key_path.is_file():
        raise RuntimeError(
            "Walmart private key file was not found at "
            f"{private_key_path}"
        )

    private_key_bytes = private_key_path.read_bytes()

    return serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
    )


def generate_walmart_headers() -> dict[str, str]:
    consumer_id = get_required_setting(
        "WALMART_CONSUMER_ID"
    )

    key_version = get_required_setting(
        "WALMART_KEY_VERSION"
    )

    timestamp = str(int(time.time() * 1000))

    string_to_sign = (
        f"{consumer_id}\n"
        f"{timestamp}\n"
        f"{key_version}\n"
    )

    private_key = load_walmart_private_key()

    signature_bytes = private_key.sign(
        string_to_sign.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    encoded_signature = base64.b64encode(
        signature_bytes
    ).decode("utf-8")

    return {
        "WM_CONSUMER.ID": consumer_id,
        "WM_CONSUMER.INTIMESTAMP": timestamp,
        "WM_SEC.KEY_VERSION": key_version,
        "WM_SEC.AUTH_SIGNATURE": encoded_signature,
        "Accept": "application/json",
        "User-Agent": "Budget-App/1.0",
    }


def lookup_walmart_product(
    upc: str,
    zip_code: str | None = None,
) -> dict:
    cleaned_upc = upc.strip()

    if not UPC_PATTERN.fullmatch(cleaned_upc):
        raise ValueError(
            "A Walmart UPC must contain exactly 12 digits"
        )

    api_base_url = get_required_setting(
        "WALMART_API_BASE_URL"
    ).rstrip("/")

    request_url = (
        f"{api_base_url}{PRODUCT_LOOKUP_PATH}"
    )

    query_parameters = {
        "upc": cleaned_upc,
    }

    if zip_code is not None:
        cleaned_zip_code = zip_code.strip()

        if cleaned_zip_code:
            query_parameters["zipCode"] = (
                cleaned_zip_code
            )

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            request_url,
            params=query_parameters,
            headers=generate_walmart_headers(),
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise RuntimeError(
            "Walmart Product Lookup failed with "
            f"HTTP {response.status_code}: "
            f"{response.text[:500]}"
        ) from error

    return response.json()


if __name__ == "__main__":
    product_result = lookup_walmart_product(
        "007874205305"
    )

    print(
        json.dumps(
            product_result,
            indent=2,
        )
    )
