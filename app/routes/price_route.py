from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.handlers.permissions_handler import (
    with_permission_and_company_from_body_check,
)
from tiacore_lib.utils.validate_helpers import validate_company_access
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.database.models import Price, PriceDetail
from app.pydantic_models.price_models import (
    PriceBulkCreateSchema,
    PriceCreateSchema,
    PriceEditSchema,
    PriceListResponseSchema,
    PriceResponseSchema,
    PriceSchema,
    price_filter_params,
)

price_router = APIRouter()

Q3 = Decimal("0.001")  # веса: 3 знака
Q2 = Decimal("0.01")  # деньги: 2 знака


def q3(x: Decimal) -> Decimal:
    return x.quantize(Q3, rounding=ROUND_HALF_UP)


def q2(x: Decimal) -> Decimal:
    return x.quantize(Q2, rounding=ROUND_HALF_UP)


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


@price_router.post(
    "/add-bulk",
    response_model=PriceResponseSchema,
    summary="Создать цену и добавить прайс-детали (bulk)",
    status_code=status.HTTP_201_CREATED,
)
async def add_price_with_details(
    data: PriceBulkCreateSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("add_price")),
):
    """
    Создаёт Price и связанные PriceDetail за один запрос.
    Правила валидации:
      - как минимум один detail обязателен
      - weight_from <= weight_to
      - weight_extra > 0
      - диапазоны отсортированы по weight_from и НЕ перекрываются (prev.weight_to < next.weight_from)
    Все числовые значения квантуются: веса — до 0.001, деньги — до 0.01.
    """
    if not data.details:
        raise HTTPException(status_code=422, detail="Нужно указать хотя бы один диапазон (details)")

    # подготовим и проверим диапазоны на стороне приложения
    prepared = []
    for i, d in enumerate(data.details, start=1):
        wf = q3(Decimal(str(d.weight_from)))
        wt = q3(Decimal(str(d.weight_to)))
        we = q3(Decimal(str(d.weight_extra)))
        vf = q2(Decimal(str(d.value_fix)))
        ve = q2(Decimal(str(d.value_extra)))

        if wf > wt:
            raise HTTPException(status_code=422, detail=f"[details[{i}]] weight_from ({wf}) > weight_to ({wt})")
        if we <= Decimal("0"):
            raise HTTPException(status_code=422, detail=f"[details[{i}]] weight_extra должен быть > 0")

        prepared.append(
            {
                "company_id": d.company_id,  # может быть None, подставим позже
                "weight_from": wf,
                "weight_to": wt,
                "weight_extra": we,
                "value_fix": vf,
                "value_extra": ve,
            }
        )

    # сортируем по нижней границе
    prepared.sort(key=lambda x: (x["weight_from"], x["weight_to"]))

    # проверка на перекрытия: требуем strict — prev.weight_to < next.weight_from
    prev_to: Optional[Decimal] = None
    for i, band in enumerate(prepared, start=1):
        if prev_to is not None and band["weight_from"] <= prev_to:
            raise HTTPException(
                status_code=422,
                detail=f"Перекрытие диапазонов: details[{i - 1}].weight_to={prev_to} "
                f"и details[{i}].weight_from={band['weight_from']}",
            )
        prev_to = band["weight_to"]

    # транзакция: и Price, и все PriceDetail атомарно
    async with in_transaction() as conn:
        price = await Price.create(
            created_by=context["user_id"],
            modified_by=context["user_id"],
            using_db=conn,
            **data.model_dump(exclude={"details"}, exclude_unset=True),
        )

        # bulk_create PriceDetail
        rows = []
        for band in prepared:
            rows.append(
                PriceDetail(
                    created_by=context["user_id"],
                    modified_by=context["user_id"],
                    price_id=price.id,
                    company_id=band["company_id"] or data.company_id,  # подставляем из Price при отсутствии
                    weight_from=band["weight_from"],
                    weight_to=band["weight_to"],
                    weight_extra=band["weight_extra"],
                    value_fix=band["value_fix"],
                    value_extra=band["value_extra"],
                )
            )

        if rows:
            await PriceDetail.bulk_create(rows, using_db=conn)

    logger.success(f"цена ({price.id}) и {len(rows)} диапазонов успешно созданы")
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
