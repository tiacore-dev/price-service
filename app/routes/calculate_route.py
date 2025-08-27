from fastapi import APIRouter, Body, Depends
from tiacore_lib.handlers.auth_handler import get_current_user

from app.pydantic_models.calculate_models import GetPriceIDResponseSchema, GetPriceIDSchema
from app.utils.get_price_id import get_price_id

calculate_router = APIRouter()


@calculate_router.post(
    "/get-price-id",
    response_model=GetPriceIDResponseSchema,
    summary="Получение цены по набору",
)
async def get_price_id_route(
    data: GetPriceIDSchema = Body(...),
    context=Depends(get_current_user),
):
    price_data = data.model_dump()
    price_id = await get_price_id(**price_data)
    return GetPriceIDResponseSchema(price_id=price_id)
