import base64
import requests
from typing import Any

from app.settings import settings


def _auth_header() -> str:
    token = base64.b64encode(
        f"{settings.PAYKEEPER_USER}:{settings.PAYKEEPER_PASSWORD}".encode("utf-8")
    ).decode("utf-8")
    return f"Basic {token}"


def get_security_token() -> str:
    """
    GET /info/settings/token/ with Basic auth
    Returns token that must be sent as POST parameter token in every POST request.
    Token changes примерно раз в 24 часа.
    """
    url = f"{settings.PAYKEEPER_BASE_URL.rstrip('/')}/info/settings/token/"
    r = requests.get(url, headers={"Authorization": _auth_header()}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "token" not in data:
        raise RuntimeError(f"PayKeeper token response invalid: {data}")
    return data["token"]


def create_invoice_preview(
    *,
    pay_amount: float,
    clientid: str,
    orderid: str,
    service_name: str,
    client_email: str | None = None,
    client_phone: str | None = None,
) -> dict[str, Any]:
    """
    POST /change/invoice/preview/ as application/x-www-form-urlencoded
    Must include token parameter.
    Returns invoice_id; pay link is BASE_URL/bill/{invoice_id}/
    """
    token = get_security_token()
    url = f"{settings.PAYKEEPER_BASE_URL.rstrip('/')}/change/invoice/preview/"

    payload = {
        "pay_amount": f"{pay_amount:.2f}",
        "clientid": clientid,
        "orderid": orderid,
        "service_name": service_name,
        "token": token,
    }
    if client_email:
        payload["client_email"] = client_email
    if client_phone:
        payload["client_phone"] = client_phone

    r = requests.post(
        url,
        headers={
            "Authorization": _auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=payload,
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()

    # PayKeeper может вернуть ошибку формата {"result":"fail","msg":"..."}
    if data.get("result") == "fail":
        raise RuntimeError(f"PayKeeper error: {data.get('msg')}")

    if "invoice_id" not in data:
        raise RuntimeError(f"PayKeeper preview response invalid: {data}")

    return data


def build_pay_url(invoice_id: str) -> str:
    return f"{settings.PAYKEEPER_BASE_URL.rstrip('/')}/bill/{invoice_id}/"


