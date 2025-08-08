import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field


class PriceDetailCreateSchema(BaseModel):
    price_id: UUID
    company_id: UUID

    weight_from: Decimal = Field(..., ge=0)
    weight_to: Decimal = Field(..., ge=0.01)
    weight_extra: Decimal = Field(..., ge=0.01)

    value_fix: Decimal
    value_extra: Decimal

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceDetailEditSchema(BaseModel):
    price_id: Optional[UUID] = Field(None)
    company_id: Optional[UUID] = Field(None)

    weight_from: Optional[Decimal] = Field(None, ge=0)
    weight_to: Optional[Decimal] = Field(None, ge=0.01)
    weight_extra: Optional[Decimal] = Field(None, ge=0.01)

    value_fix: Optional[Decimal] = Field(None, ge=0.01)
    value_extra: Optional[Decimal] = Field(None, ge=0.01)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceDetailSchema(BaseModel):
    id: UUID = Field(..., alias="price_detail_id")
    price_id: UUID
    company_id: UUID

    weight_from: float
    weight_to: float
    weight_extra: float

    value_fix: float
    value_extra: float

    created_at: datetime.datetime = Field(...)
    created_by: UUID = Field(...)
    modified_at: datetime.datetime = Field(...)
    modified_by: UUID = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceDetailResponseSchema(BaseModel):
    price_detail_id: UUID


class PriceDetailListResponseSchema(BaseModel):
    total: int
    details: List[PriceDetailSchema]


def price_detail_filter_params(
    price_id: Optional[str] = Query(None),
    company_id: Optional[UUID] = Query(None, description="Фильтр по компании"),
    sort_by: Literal["created_at"] = Query("created_at", description="Поле сортировки"),
    order: Literal["asc", "desc"] = Query("asc", description="asc/desc"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
):
    return {
        "price_id": price_id,
        "company_id": company_id,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
