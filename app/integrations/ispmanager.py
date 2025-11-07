from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger("app.integrations.ispmanager")


class ISPManagerError(Exception):
    """Исключение, возникающее при ошибках взаимодействия с ISPmanager."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


@dataclass
class ISPManagerClient:
    """Минимальный клиент для взаимодействия с ISPmanager API."""

    base_url: str = settings.isp_api_base_url.rstrip("/")
    token: Optional[str] = settings.isp_api_token
    timeout: float = 10.0

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Content-Type", "application/json")

        params = kwargs.setdefault("params", {})
        params.setdefault("out", "json")

        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")
        else:
            if not settings.isp_admin_login or not settings.isp_admin_password:
                raise ISPManagerError("Не заданы параметры isp_admin_login / isp_admin_password для authinfo")
            params.setdefault(
                "authinfo",
                f"{settings.isp_admin_login}:{settings.isp_admin_password}",
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:  # pragma: no cover - network errors
            logger.error("ISPmanager request failed: %s", exc)
            raise ISPManagerError("Недоступен ISPmanager API") from exc

        if response.status_code >= 400:
            logger.warning(
                "ISPmanager responded with error",
                extra={"status_code": response.status_code, "body": response.text},
            )
            payload: Dict[str, Any]
            if response.headers.get("content-type", "").startswith("application/json"):
                payload = response.json()
            else:
                payload = {"body": response.text}
            raise ISPManagerError(
                message="Ошибка при обращении к ISPmanager",
                status_code=response.status_code,
                payload=payload,
            )

        if not response.content:
            return {}

        if "application/json" in response.headers.get("content-type", ""):
            return response.json()

        return {"raw": response.text}

    async def create_account(self, *, email: str, username: str, password: str, first_name: str = "", last_name: str = "", phone: str = "") -> Dict[str, Any]:
        payload = {
            "email": email,
            "username": username,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
        }
        return await self._request("POST", "/v1/accounts", json=payload)

    async def create_ftp_user(self, *, account_id: str, username: str, password: str, home_directory: str) -> Dict[str, Any]:
        payload = {
            "account_id": account_id,
            "username": username,
            "password": password,
            "home_directory": home_directory,
        }
        return await self._request("POST", "/v1/ftp-users", json=payload)

    async def create_domain(self, *, account_id: str, domain_name: str, nameservers: Optional[list[str]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "account_id": account_id,
            "domain": domain_name,
        }
        if nameservers:
            payload["nameservers"] = nameservers
        return await self._request("POST", "/v1/domains", json=payload)

    async def create_dns_record(self, *, domain_id: str, record_type: str, name: str, value: str, ttl: int = 3600, priority: Optional[int] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "domain_id": domain_id,
            "type": record_type,
            "name": name,
            "value": value,
            "ttl": ttl,
        }
        if priority is not None:
            payload["priority"] = priority
        return await self._request("POST", "/v1/dns-records", json=payload)

    async def create_site(self, *, account_id: str, root_path: str, domain: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "account_id": account_id,
            "root_path": root_path,
        }
        if domain:
            payload["domain"] = domain
        return await self._request("POST", "/v1/sites", json=payload)

    async def delete_domain(self, *, domain_id: str) -> Dict[str, Any]:
        return await self._request("DELETE", f"/v1/domains/{domain_id}")

    async def delete_dns_record(self, *, record_id: str) -> Dict[str, Any]:
        return await self._request("DELETE", f"/v1/dns-records/{record_id}")

    async def delete_site(self, *, site_id: str) -> Dict[str, Any]:
        return await self._request("DELETE", f"/v1/sites/{site_id}")


def extract_identifier(payload: Dict[str, Any], *candidate_keys: str) -> str:
    if not payload:
        raise ISPManagerError("Пустой ответ от ISPmanager")

    keys = list(candidate_keys) + [
        "id",
        "account_id",
        "ftp_id",
        "domain_id",
        "record_id",
        "identifier",
        "uuid",
    ]

    for key in keys:
        if key in payload and payload[key]:
            return str(payload[key])

    raise ISPManagerError("В ответе ISPmanager нет идентификатора", payload=payload)


def get_isp_client() -> ISPManagerClient:
    return ISPManagerClient()

