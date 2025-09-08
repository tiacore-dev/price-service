from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from tiacore_lib.handlers.auth_handler import get_current_user

from app.database.models import Price, PriceDetail
from app.handlers.calculate_handler import InvalidPriceDetail, PriceRangeNotFound, compute_quote_amount
from app.pydantic_models.calculate_models import GetPriceIDResponseSchema, GetPriceIDSchema, QuoteRequest, QuoteResponse
from app.utils.get_price_id import get_price_id

calculate_router = APIRouter()

ZERO = Decimal("0.00")


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

    # нет ни одной строки — просто 0
    if not details:
        return QuoteResponse(summ=ZERO)  # id=None, increments=0 по умолчанию

    try:
        # здесь без fallback — если вне диапазонов, вернём 0
        result = compute_quote_amount(
            base_value=body.base_value,
            price_details=details,
            fallback_to_top_if_out_of_range=False,
        )
    except PriceRangeNotFound:
        # base_value не попал ни в один диапазон — просто 0
        return QuoteResponse(summ=ZERO)
    except InvalidPriceDetail as e:
        # поломанные данные прайса — это наша ошибка конфигурации
        raise HTTPException(status_code=400, detail=str(e))

    return QuoteResponse(
        summ=result.total_amount,
        price_detail_id=result.price_detail_id,
        extra_increments=result.extra_increments,
    )
