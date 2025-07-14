import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field


class PriceSetRelationCreateSchema(BaseModel):
    price_id: UUID = Field(..., alias="price_id")
    price_set_id: UUID = Field(..., alias="price_set_id")
    company_id: UUID = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSetRelationEditSchema(BaseModel):
    price_id: Optional[UUID] = Field(None, alias="price_id")
    price_set_id: Optional[UUID] = Field(None, alias="price_set_id")
    company_id: Optional[UUID] = Field(None)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSetRelationSchema(BaseModel):
    id: UUID = Field(..., alias="relation_id")
    price_id: UUID = Field(..., alias="price_id")
    price_set_id: UUID = Field(..., alias="price_set_id")
    company_id: UUID = Field(...)

    created_at: datetime.datetime = Field(...)
    created_by: UUID = Field(...)
    modified_at: datetime.datetime = Field(...)
    modified_by: UUID = Field(...)

    class Config:
        from_attributes = True
        populate_by_name = True


class PriceSetRelationResponseSchema(BaseModel):
    relation_id: UUID


class PriceSetRelationListResponseSchema(BaseModel):
    total: int
    relations: List[PriceSetRelationSchema]


def price_set_relation_filter_params(
    price_id: Optional[UUID] = Query(None, description="Фильтр по ID цены"),
    price_set_id: Optional[UUID] = Query(None, description="Фильтр по ID набора цен"),
    company_id: Optional[UUID] = Query(None, description="Фильтр по компании"),
    sort_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order: Optional[str] = Query("asc", description="asc / desc"),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
):
    return {
        "price_id": price_id,
        "price_set_id": price_set_id,
        "company_id": company_id,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
