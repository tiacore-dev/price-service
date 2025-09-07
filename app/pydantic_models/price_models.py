import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field

from app.database.models import ServiceType


class PriceCreateSchema(BaseModel):
    price_category_id: UUID = Field(...)
    company_id: UUID = Field(...)
    sender_city: UUID = Field(...)
    sender_warehouse: Optional[UUID] = Field(None)
    recipient_city: UUID = Field(...)
    recipient_warehouse: Optional[UUID] = Field(None)
    comment: Optional[str] = Field(None)
    delivery_duration: int = Field(...)
    service_type: ServiceType = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceDetailItemCreateSchema(BaseModel):
    # если не передан — возьмём из родительской цены
    company_id: Optional[UUID] = None

    # веса — 3 знака после запятой по схеме
    weight_from: Decimal = Field(..., ge=0)
    weight_to: Decimal = Field(..., ge=0.01)
    weight_extra: Decimal = Field(..., ge=0.01)

    # деньги — 2 знака после запятой
    value_fix: Decimal = Field(..., ge=0.01)
    value_extra: Decimal = Field(..., ge=0)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceBulkCreateSchema(BaseModel):
    price_category_id: UUID = Field(...)
    company_id: UUID = Field(...)
    sender_city: UUID = Field(...)
    sender_warehouse: Optional[UUID] = Field(None)
    recipient_city: UUID = Field(...)
    recipient_warehouse: Optional[UUID] = Field(None)
    comment: Optional[str] = Field(None)
    delivery_duration: int = Field(...)
    service_type: ServiceType = Field(...)
    details: List[PriceDetailItemCreateSchema]


class PriceEditSchema(BaseModel):
    price_category_id: Optional[UUID] = Field(None)
    company_id: Optional[UUID] = Field(None)
    sender_city: Optional[UUID] = Field(None)
    sender_warehouse: Optional[UUID] = Field(None)
    recipient_city: Optional[UUID] = Field(None)
    recipient_warehouse: Optional[UUID] = Field(None)
    comment: Optional[str] = Field(None)
    delivery_duration: Optional[int] = Field(None)
    service_type: Optional[ServiceType] = Field(None)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSchema(BaseModel):
    id: UUID = Field(..., alias="price_id")
    price_category_id: UUID = Field(...)
    company_id: UUID = Field(...)
    sender_city: UUID = Field(...)
    sender_warehouse: Optional[UUID] = Field(None)
    recipient_city: UUID = Field(...)
    recipient_warehouse: Optional[UUID] = Field(None)
    comment: Optional[str] = Field(None)
    delivery_duration: int
    service_type: ServiceType = Field(...)

    created_at: datetime.datetime = Field(...)
    created_by: UUID = Field(...)
    modified_at: datetime.datetime = Field(...)
    modified_by: UUID = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceResponseSchema(BaseModel):
    price_id: UUID


class PriceListResponseSchema(BaseModel):
    total: int
    prices: List[PriceSchema]


def price_filter_params(
    company_id: Optional[UUID] = Query(None, description="Фильтр по компании"),
    price_category_id: Optional[UUID] = Query(None),
    sender_city: Optional[UUID] = Query(None),
    sender_warehouse: Optional[UUID] = Query(None),
    recipient_city: Optional[UUID] = Query(None),
    recipient_warehouse: Optional[UUID] = Query(None),
    service_type: Optional[ServiceType] = Query(None),
    sort_by: Literal["created_at", "delivery_duration"] = Query("created_at", description="Поле сортировки"),
    order: Literal["asc", "desc"] = Query("asc", description="asc/desc"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
):
    return {
        "price_category_id": price_category_id,
        "sender_city": sender_city,
        "company_id": company_id,
        "sender_warehouse": sender_warehouse,
        "recipient_city": recipient_city,
        "recipient_warehouse": recipient_warehouse,
        "service_type": service_type,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
