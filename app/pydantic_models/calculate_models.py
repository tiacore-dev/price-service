from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from tiacore_lib.enums import ServiceType


class GetPriceIDSchema(BaseModel):
    price_set_id: UUID
    sender_city_id: UUID
    recipient_city_id: UUID
    sender_warehouse_id: Optional[UUID] = Field(None)
    recipient_warehouse_id: Optional[UUID] = Field(None)
    service_type: ServiceType

    class Config:
        from_attributes = True


class GetPriceIDResponseSchema(BaseModel):
    price_id: Optional[UUID] = Field(None)
