from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.integrations import ISPManagerError, extract_identifier, get_isp_client
from app.modules.auth.models import AuthUsers
from app.modules.auth.routes import get_current_user
from app.modules.domains.models import DNSRecord, Domain
from app.modules.domains.schemas import (
    DNSRecordCreate,
    DNSRecordResponse,
    DomainCreate,
    DomainResponse,
    DomainStatus,
    DomainUpdate,
)

router = APIRouter()


def _ensure_remote_binding(user: AuthUsers) -> None:
    if not user.isp_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для пользователя не настроена учетная запись в ISPmanager",
        )


async def _get_domain_or_404(db: AsyncSession, domain_id: int, user: AuthUsers) -> Domain:
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.user_id == user.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Домен не найден")
    return domain


@router.get("/domains", response_model=List[DomainResponse])
async def get_user_domains(
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    query = (
        select(Domain)
        .where(Domain.user_id == current_user.id)
        .order_by(Domain.registered_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/domains", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    domain_data: DomainCreate,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_remote_binding(current_user)

    normalized_name = domain_data.name.lower().strip()

    existing = await db.execute(select(Domain).where(Domain.name == normalized_name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Домен уже существует")

    domain = Domain(
        user_id=current_user.id,
        name=normalized_name,
        auto_renew=domain_data.auto_renew,
        status=DomainStatus.PENDING.value,
        nameservers=domain_data.nameservers,
    )
    db.add(domain)
    await db.flush()

    isp_client = get_isp_client()

    try:
        isp_response = await isp_client.create_domain(
            account_id=current_user.isp_account_id,
            domain_name=domain.name,
            nameservers=domain_data.nameservers,
        )
        domain.isp_domain_id = extract_identifier(isp_response, "domain_id")
        status_value = isp_response.get("status")
        if isinstance(status_value, str):
            normalized = status_value.lower()
            if normalized in {status.value for status in DomainStatus}:
                domain.status = normalized
        await db.commit()
    except ISPManagerError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ISPmanager отклонил создание домена",
        ) from exc
    except Exception:
        await db.rollback()
        raise
    else:
        await db.refresh(domain)

    return domain


@router.get("/domains/{domain_id}", response_model=DomainResponse)
async def get_domain_details(
    domain_id: int,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    domain = await _get_domain_or_404(db, domain_id, current_user)
    return domain


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: int,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    domain = await _get_domain_or_404(db, domain_id, current_user)

    isp_client = get_isp_client()

    try:
        if domain.isp_domain_id:
            await isp_client.delete_domain(domain_id=domain.isp_domain_id)
        await db.execute(delete(Domain).where(Domain.id == domain.id))
        await db.commit()
    except ISPManagerError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось удалить домен в ISPmanager",
        ) from exc


@router.post("/domains/{domain_id}/dns", response_model=DNSRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_dns_record(
    domain_id: int,
    dns_data: DNSRecordCreate,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    domain = await _get_domain_or_404(db, domain_id, current_user)

    if not domain.isp_domain_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Домен не связан с ISPmanager")

    isp_client = get_isp_client()

    try:
        isp_response = await isp_client.create_dns_record(
            domain_id=domain.isp_domain_id,
            record_type=dns_data.record_type.value,
            name=dns_data.name,
            value=dns_data.value,
            ttl=dns_data.ttl,
            priority=dns_data.priority,
        )

        record = DNSRecord(
            domain_id=domain.id,
            record_type=dns_data.record_type.value,
            name=dns_data.name,
            value=dns_data.value,
            ttl=dns_data.ttl,
            priority=dns_data.priority,
            isp_record_id=extract_identifier(isp_response, "record_id"),
        )
        db.add(record)
        await db.commit()
    except ISPManagerError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ISPmanager отклонил создание записи",
        ) from exc
    else:
        await db.refresh(record)

    return record


@router.get("/domains/{domain_id}/dns", response_model=List[DNSRecordResponse])
async def get_dns_records(
    domain_id: int,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_domain_or_404(db, domain_id, current_user)
    result = await db.execute(
        select(DNSRecord).where(DNSRecord.domain_id == domain_id).order_by(DNSRecord.created_at.desc())
    )
    return result.scalars().all()