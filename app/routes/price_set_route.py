from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.handlers.permissions_handler import with_permission_and_company_from_body_check
from tiacore_lib.utils.validate_helpers import validate_company_access
from tortoise.expressions import Q

from app.database.models import PriceSet
from app.pydantic_models.price_set_models import (
    PriceSetCreateSchema,
    PriceSetEditSchema,
    PriceSetListResponseSchema,
    PriceSetResponseSchema,
    PriceSetSchema,
    price_set_filter_params,
)

price_set_router = APIRouter()


@price_set_router.post(
    "/add",
    response_model=PriceSetResponseSchema,
    summary="Добавление нового набора цен",
    status_code=status.HTTP_201_CREATED,
)
async def add_price_set(
    data: PriceSetCreateSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("add_price_set")),
):
    price_set = await PriceSet.create(
        created_by=context["user_id"],
        modified_by=context["user_id"],
        **data.model_dump(exclude_unset=True),
    )
    if not price_set:
        logger.error("Не удалось создать набор цен")
        raise HTTPException(status_code=500, detail="Не удалось создать набор цен")

    logger.success(f"Набор цен {price_set.name} ({price_set.id}) успешно создан")
    return PriceSetResponseSchema(price_set_id=price_set.id)


@price_set_router.patch(
    "/{price_set_id}",
    summary="Изменение набора цен",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def edit_price_set(
    price_set_id: UUID = Path(..., title="ID набора цен", description="ID изменяемого набора цен"),
    data: PriceSetEditSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("edit_price_set")),
):
    logger.info(f"Обновление набора цен {price_set_id}")

    price_set = await PriceSet.filter(id=price_set_id).first()
    if not price_set:
        logger.warning(f"Набор цен {price_set_id} не найден")
        raise HTTPException(status_code=404, detail="Набор цен не найден")

    validate_company_access(price_set, context, "набор цен")
    price_set.modified_by = context["user_id"]
    await price_set.update_from_dict(data.model_dump(exclude_unset=True))
    await price_set.save()


@price_set_router.delete(
    "/{price_set_id}",
    summary="Удаление набора цен",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_price_set(
    price_set_id: UUID = Path(..., title="ID набора цен", description="ID удаляемого набора цен"),
    context=Depends(require_permission_in_context("delete_price_set")),
):
    price_set = await PriceSet.filter(id=price_set_id).first()
    if not price_set:
        logger.warning(f"Набор цен {price_set_id} не найден")
        raise HTTPException(status_code=404, detail="Набор цен не найден")
    validate_company_access(price_set, context, "набор цен")
    await price_set.delete()


@price_set_router.get(
    "/all",
    response_model=PriceSetListResponseSchema,
    summary="Получение списка наборов цен с фильтрацией",
)
async def get_price_sets(
    filters: dict = Depends(price_set_filter_params),
    context=Depends(require_permission_in_context("get_all_price_sets")),
):
    query = Q()

    if filters.get("company_id"):
        query &= Q(company_id=filters["company_id"])
    if filters.get("price_set_name"):
        query &= Q(name__icontains=filters["price_set_name"])

    sort_by = filters.get("sort_by", "created_at")
    if sort_by == "price_set_name":
        sort_by = "name"
    order_by = f"{'-' if filters.get('order') == 'desc' else ''}{sort_by}"
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 10)

    total_count = await PriceSet.filter(query).count()
    price_sets = await PriceSet.filter(query).order_by(order_by).offset((page - 1) * page_size).limit(page_size)

    return PriceSetListResponseSchema(
        total=total_count,
        price_sets=[PriceSetSchema.model_validate(ps) for ps in price_sets],
    )


@price_set_router.get(
    "/{price_set_id}",
    response_model=PriceSetSchema,
    summary="Просмотр набора цен",
)
async def get_price_set(
    price_set_id: UUID = Path(..., title="ID набора цен", description="ID просматриваемого набора цен"),
    context=Depends(require_permission_in_context("view_price_set")),
):
    logger.info(f"Запрос на просмотр набора цен: {price_set_id}")
    price_set = await PriceSet.filter(id=price_set_id).first()

    if price_set is None:
        logger.warning(f"Набор цен {price_set_id} не найден")
        raise HTTPException(status_code=404, detail="Набор цен не найден")
    validate_company_access(price_set, context, "набор цен")

    price_set_schema = PriceSetSchema.model_validate(price_set)
    logger.success(f"Набор цен найден: {price_set_schema}")
    return price_set_schema
