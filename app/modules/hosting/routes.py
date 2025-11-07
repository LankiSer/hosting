from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.integrations import ISPManagerError, extract_identifier, get_isp_client
from app.modules.auth.models import AuthUsers
from app.modules.auth.routes import get_current_user
from app.modules.domains.models import Domain
from app.modules.hosting.models import HostingAccount, HostingSite
from app.modules.hosting.schemas import HostingAccountResponse, HostingSiteCreate, HostingSiteResponse, SiteStatus

router = APIRouter()


def _ensure_hosting_account(user: AuthUsers) -> HostingAccount:
    if not user.hosting_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FTP аккаунт не найден")
    return user.hosting_account


def _ensure_remote_binding(user: AuthUsers) -> str:
    if not user.isp_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Для пользователя не настроена учетная запись в ISPmanager")
    return user.isp_account_id


async def _get_site_or_404(db: AsyncSession, site_id: int, user: AuthUsers) -> HostingSite:
    result = await db.execute(
        select(HostingSite).where(HostingSite.id == site_id, HostingSite.user_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сайт не найден")
    return site


async def _get_domain_for_user(db: AsyncSession, domain_id: int, user: AuthUsers) -> Domain:
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.user_id == user.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Домен не найден")
    return domain


@router.get("/hosting/account/ftp", response_model=HostingAccountResponse)
async def get_ftp_account(current_user: AuthUsers = Depends(get_current_user)):
    _ensure_hosting_account(current_user)
    return HostingAccountResponse.model_validate(account, from_attributes=True)


@router.get("/hosting/sites", response_model=List[HostingSiteResponse])
async def get_user_sites(
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    query = (
        select(HostingSite)
        .where(HostingSite.user_id == current_user.id)
        .order_by(HostingSite.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/hosting/sites", response_model=HostingSiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: HostingSiteCreate,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = _ensure_hosting_account(current_user)
    remote_account_id = _ensure_remote_binding(current_user)

    domain = None
    if site_data.domain_id is not None:
        domain = await _get_domain_for_user(db, site_data.domain_id, current_user)

    isp_client = get_isp_client()

    site = HostingSite(
        user_id=current_user.id,
        domain_id=domain.id if domain else None,
        root_path=site_data.root_path,
        status=SiteStatus.ACTIVE.value,
    )
    db.add(site)
    await db.flush()

    payload = {
        "account_id": remote_account_id,
        "root_path": site_data.root_path,
    }
    if domain:
        payload["domain"] = domain.name

    try:
        isp_response = await isp_client.create_site(**payload)
        site.isp_site_id = extract_identifier(isp_response, "site_id")
        status_value = isp_response.get("status")
        if isinstance(status_value, str):
            normalized = status_value.lower()
            if normalized in {status.value for status in SiteStatus}:
                site.status = normalized
        await db.commit()
    except ISPManagerError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ISPmanager отклонил создание сайта") from exc
    else:
        await db.refresh(site)

    return site


@router.get("/hosting/sites/{site_id}", response_model=HostingSiteResponse)
async def get_site_details(
    site_id: int,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await _get_site_or_404(db, site_id, current_user)
    return site


@router.delete("/hosting/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: int,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await _get_site_or_404(db, site_id, current_user)

    isp_client = get_isp_client()

    try:
        if site.isp_site_id:
            await isp_client.delete_site(site_id=site.isp_site_id)
        await db.execute(delete(HostingSite).where(HostingSite.id == site.id))
        await db.commit()
    except ISPManagerError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Не удалось удалить сайт в ISPmanager") from exc