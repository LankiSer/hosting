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
    """Минимальный клиент для взаимодействия с классическим API ISPmanager."""

    base_url: str = settings.isp_api_base_url.rstrip("/")
    token: Optional[str] = settings.isp_api_token
    timeout: float = 10.0

    def __post_init__(self) -> None:
        if not self.base_url.lower().endswith("/ispmgr"):
            self.base_url = f"{self.base_url.rstrip('/')}/ispmgr"

    def _build_url(self, path: str | None = None) -> str:
        if not path:
            return self.base_url
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url.rstrip('/')}{path}"

    async def _request(
        self,
        method: str = "GET",
        path: Optional[str] = None,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._build_url(path)
        headers: Dict[str, str] = {"Accept": "application/json"}

        request_params = dict(params or {})
        request_params.setdefault("out", "json")

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            if not settings.isp_admin_login or not settings.isp_admin_password:
                raise ISPManagerError("Не заданы параметры isp_admin_login / isp_admin_password для authinfo")
            request_params.setdefault(
                "authinfo",
                f"{settings.isp_admin_login}:{settings.isp_admin_password}",
            )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=settings.isp_verify_ssl,
            ) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=request_params,
                    data=data,
                )
                logger.debug(
                    "ISPmanager request",
                    extra={
                        "method": method,
                        "url": str(response.request.url),
                        "status": response.status_code,
                    },
                )
        except httpx.HTTPError as exc:  # pragma: no cover - network errors
            logger.error("ISPmanager request failed: %s", exc)
            raise ISPManagerError("Недоступен ISPmanager API") from exc

        if response.status_code >= 400:
            logger.warning(
                "ISPmanager responded with error",
                extra={"status_code": response.status_code, "body": response.text},
            )
            payload: Dict[str, Any]
            if "application/json" in response.headers.get("content-type", ""):
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

        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    async def create_account(
        self,
        *,
        email: str,
        username: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "func": "user.edit",
            "sok": "ok",
            "name": username,
            "passwd": password,
            "cnfmpassword": password,
            "email": email,
        }

        owner = settings.isp_admin_login or "root"
        params.setdefault("owner", owner)

        if settings.isp_default_template:
            params["preset"] = settings.isp_default_template

        comment_parts = [part for part in (first_name, last_name) if part]
        if comment_parts:
            params["comment"] = " ".join(comment_parts)

        if phone:
            params["phone"] = phone

        response = await self._request("GET", params=params)
        response.setdefault("identifier", username)
        return response

    async def create_ftp_user(
        self,
        *,
        account_id: str,
        username: str,
        password: str,
        home_directory: str,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "func": "ftp_user.edit",
            "sok": "ok",
            "name": username,
            "passwd": password,
            "cnfmpassword": password,
            "homedir": home_directory,
            "owner": account_id,
        }

        response = await self._request("GET", params=params)
        response.setdefault("identifier", username)
        return response

    async def create_domain(self, *, account_id: str, domain_name: str, nameservers: Optional[list[str]] = None) -> Dict[str, Any]:
        raise ISPManagerError("Создание домена через классический API ISPmanager пока не реализовано")

    async def create_dns_record(self, *, domain_id: str, record_type: str, name: str, value: str, ttl: int = 3600, priority: Optional[int] = None) -> Dict[str, Any]:
        raise ISPManagerError("Создание DNS-записи через классический API ISPmanager пока не реализовано")

    async def create_site(self, *, account_id: str, root_path: str, domain: Optional[str] = None) -> Dict[str, Any]:
        raise ISPManagerError("Создание сайта через классический API ISPmanager пока не реализовано")

    async def delete_domain(self, *, domain_id: str) -> Dict[str, Any]:
        raise ISPManagerError("Удаление домена через классический API ISPmanager пока не реализовано")

    async def delete_dns_record(self, *, record_id: str) -> Dict[str, Any]:
        raise ISPManagerError("Удаление DNS-записи через классический API ISPmanager пока не реализовано")

    async def delete_site(self, *, site_id: str) -> Dict[str, Any]:
        raise ISPManagerError("Удаление сайта через классический API ISPmanager пока не реализовано")


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

