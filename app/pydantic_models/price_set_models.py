import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field


class PriceSetCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, alias="price_set_name")
    company_id: UUID = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSetEditSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, alias="price_set_name")
    company_id: Optional[UUID] = Field(None)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSetSchema(BaseModel):
    id: UUID = Field(..., alias="price_set_id")
    name: str = Field(..., alias="price_set_name")
    company_id: UUID = Field(...)

    created_at: datetime.datetime = Field(...)
    created_by: UUID = Field(...)
    modified_at: datetime.datetime = Field(...)
    modified_by: UUID = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSetResponseSchema(BaseModel):
    price_set_id: UUID


class PriceSetListResponseSchema(BaseModel):
    total: int
    price_sets: List[PriceSetSchema]


def price_set_filter_params(
    price_set_name: Optional[str] = Query(None, description="Фильтр по названию набора цен"),
    company_id: Optional[UUID] = Query(None, description="Фильтр по компании"),
    sort_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order: Optional[str] = Query("asc", description="asc / desc"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
):
    return {
        "price_set_name": price_set_name,
        "company_id": company_id,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
