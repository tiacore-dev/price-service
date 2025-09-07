from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from tiacore_lib.handlers.auth_handler import get_current_user

from app.database.models import Price, PriceDetail
from app.handlers.calculate_handler import InvalidPriceDetail, compute_quote_amount
from app.pydantic_models.calculate_models import GetPriceIDResponseSchema, GetPriceIDSchema, QuoteRequest, QuoteResponse
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


@calculate_router.post("/calculate/{price_id}", response_model=QuoteResponse)
async def quote_price(price_id: UUID, body: QuoteRequest):
    price = await Price.get_or_none(id=price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Прайс не найден")

    details = await PriceDetail.filter(price_id=price_id).order_by("weight_from")

    try:
        result = compute_quote_amount(
            body.base_value,
            details,
            fallback_to_top_if_out_of_range=True,
        )
    except InvalidPriceDetail as e:
        raise HTTPException(status_code=400, detail=str(e))

    return QuoteResponse(
        summ=result.total_amount,
        price_detail_id=result.price_detail_id,
        extra_increments=result.extra_increments,
    )
