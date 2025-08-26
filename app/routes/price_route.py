from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.handlers.permissions_handler import (
    with_permission_and_company_from_body_check,
)
from tiacore_lib.utils.validate_helpers import validate_company_access
from tortoise.expressions import Q

from app.database.models import Price
from app.pydantic_models.price_models import (
    PriceCreateSchema,
    PriceEditSchema,
    PriceListResponseSchema,
    PriceResponseSchema,
    PriceSchema,
    price_filter_params,
)

price_router = APIRouter()


@price_router.post(
    "/add",
    response_model=PriceResponseSchema,
    summary="Добавление новой цены",
    status_code=status.HTTP_201_CREATED,
)
async def add_price(
    data: PriceCreateSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("add_price")),
):
    price = await Price.create(
        created_by=context["user_id"],
        modified_by=context["user_id"],
        **data.model_dump(exclude_unset=True),
    )
    if not price:
        logger.error("Не удалось создать цену")
        raise HTTPException(status_code=500, detail="Не удалось создать цену")

    logger.success(f"цена ({price.id}) успешно создан")
    return PriceResponseSchema(price_id=price.id)


@price_router.patch(
    "/{price_id}",
    summary="Изменение цены",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def edit_price(
    price_id: UUID = Path(..., title="ID цены", description="ID изменяемой цены"),
    data: PriceEditSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("edit_price")),
):
    logger.info(f"Обновление цены {price_id}")

    price = await Price.filter(id=price_id).first()
    if not price:
        logger.warning(f"цена {price_id} не найдена")
        raise HTTPException(status_code=404, detail="Цена не найдена")

    validate_company_access(price, context, "цена")
    price.modified_by = context["user_id"]
    await price.update_from_dict(data.model_dump(exclude_unset=True))
    await price.save()


@price_router.delete(
    "/{price_id}",
    summary="Удаление цены",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_price(
    price_id: UUID = Path(..., title="ID цены", description="ID удаляемой цены"),
    context=Depends(require_permission_in_context("delete_price")),
):
    price = await Price.filter(id=price_id).first()
    if not price:
        logger.warning(f"цена {price_id} не найдена")
        raise HTTPException(status_code=404, detail="цена не найдена")
    validate_company_access(price, context, "цена")
    await price.delete()


@price_router.get(
    "/all",
    response_model=PriceListResponseSchema,
    summary="Получение списка ценуов с фильтрацией",
)
async def get_prices(
    filters: dict = Depends(price_filter_params),
    context=Depends(require_permission_in_context("get_all_price_categories")),
):
    query = Q()

    if filters.get("company_id"):
        query &= Q(company_id=filters.get("company_id"))
    if filters.get("price_category_id"):
        query &= Q(price_category_id=filters["price_category_id"])
    if filters.get("sender_city"):
        query &= Q(sender_city=filters["sender_city"])
    if filters.get("sender_warehouse"):
        query &= Q(sender_warehouse=filters["sender_warehouse"])
    if filters.get("recipient_city"):
        query &= Q(parent_id=filters["recipient_city"])
    if filters.get("recipient_warehouse"):
        query &= Q(nrecipient_warehouse=filters["recipient_warehouse"])
    if filters.get("service_type"):
        query &= Q(service_type=filters["service_type"])

    sort_by = filters.get("sort_by", "created_at")

    order_by = f"{'-' if filters.get('order') == 'desc' else ''}{sort_by}"
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 10)

    total_count = await Price.filter(query).count()

    prices = await Price.filter(query).order_by(order_by).offset((page - 1) * page_size).limit(page_size)

    return PriceListResponseSchema(
        total=total_count,
        prices=[PriceSchema.model_validate(price) for price in prices],
    )


@price_router.get("/{price_id}", response_model=PriceSchema, summary="Просмотр ценыы")
async def get_price(
    price_id: UUID = Path(..., title="ID ценыы", description="ID просматриваемой ценыы"),
    context=Depends(require_permission_in_context("view_price")),
):
    logger.info(f"Запрос на просмотр ценуы: {price_id}")
    price = await Price.filter(id=price_id).first()

    if price is None:
        logger.warning(f"цена {price_id} не найдена")
        raise HTTPException(status_code=404, detail="цена не найдена")
    validate_company_access(price, context, "цена")
    price_schema = PriceSchema.model_validate(price)

    logger.success(f"цена найдена: {price_schema}")
    return price_schema
