from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.handlers.permissions_handler import (
    with_permission_and_company_from_body_check,
)
from tiacore_lib.utils.validate_helpers import validate_company_access, validate_exists
from tortoise.expressions import Q

from app.database.models import Price, PriceDetail
from app.pydantic_models.price_detail_models import (
    PriceDetailCreateSchema,
    PriceDetailEditSchema,
    PriceDetailListResponseSchema,
    PriceDetailResponseSchema,
    PriceDetailSchema,
    price_detail_filter_params,
)

price_detail_router = APIRouter()


@price_detail_router.post(
    "/add",
    response_model=PriceDetailResponseSchema,
    summary="Добавление новой детали цен",
    status_code=status.HTTP_201_CREATED,
)
async def add_price_detail(
    data: PriceDetailCreateSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("add_price_detail")),
):
    await validate_exists(Price, data.price_id, "Цена")
    price_detail = await PriceDetail.create(
        created_by=context["user_id"],
        modified_by=context["user_id"],
        **data.model_dump(exclude_unset=True),
    )
    if not price_detail:
        logger.error("Не удалось создать деталь цен")
        raise HTTPException(status_code=500, detail="Не удалось создать деталь цен")

    logger.success(f"деталь цен ({price_detail.id}) успешно создан")
    return PriceDetailResponseSchema(price_detail_id=price_detail.id)


@price_detail_router.patch(
    "/{price_detail_id}",
    summary="Изменение детали цен",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def edit_price_detail(
    price_detail_id: UUID = Path(..., title="ID детали цен", description="ID изменяемой детали цен"),
    data: PriceDetailEditSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("edit_price_detail")),
):
    logger.info(f"Обновление детали цен {price_detail_id}")

    price_detail = await PriceDetail.filter(id=price_detail_id).first()
    if not price_detail:
        logger.warning(f"деталь цен {price_detail_id} не найдена")
        raise HTTPException(status_code=404, detail="Деталь цен не найдена")

    validate_company_access(price_detail, context, "деталь цен")
    if data.price_id:
        await validate_exists(Price, data.price_id, "Цена")
    price_detail.modified_by = context["user_id"]
    await price_detail.update_from_dict(data.model_dump(exclude_unset=True))
    await price_detail.save()


@price_detail_router.delete(
    "/{price_detail_id}",
    summary="Удаление детали цен",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_price_detail(
    price_detail_id: UUID = Path(..., title="ID детали цен", description="ID удаляемой детали цен"),
    context=Depends(require_permission_in_context("delete_price_detail")),
):
    price_detail = await PriceDetail.filter(id=price_detail_id).first()
    if not price_detail:
        logger.warning(f"деталь цен {price_detail_id} не найдена")
        raise HTTPException(status_code=404, detail="деталь цен не найдена")
    validate_company_access(price_detail, context, "деталь цен")
    await price_detail.delete()


@price_detail_router.get(
    "/all",
    response_model=PriceDetailListResponseSchema,
    summary="Получение списка деталь ценов с фильтрацией",
)
async def get_price_details(
    filters: dict = Depends(price_detail_filter_params),
    context=Depends(require_permission_in_context("get_all_price_details")),
):
    query = Q()

    if filters.get("company_id"):
        query &= Q(company_id=filters.get("company_id"))
    if filters.get("price_id"):
        query &= Q(price_id=filters.get("price_id"))
    if filters.get("price_detail_name"):
        query &= Q(name__icontains=filters["price_detail_name"])

    sort_by = filters.get("sort_by", "created_at")

    order_by = f"{'-' if filters.get('order') == 'desc' else ''}{sort_by}"
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 10)

    total_count = await PriceDetail.filter(query).count()

    price_details = await PriceDetail.filter(query).order_by(order_by).offset((page - 1) * page_size).limit(page_size)

    return PriceDetailListResponseSchema(
        total=total_count,
        details=[PriceDetailSchema.model_validate(price_detail) for price_detail in price_details],
    )


@price_detail_router.get("/{price_detail_id}", response_model=PriceDetailSchema, summary="Просмотр детали цены")
async def get_price_detail(
    price_detail_id: UUID = Path(..., title="ID детали цены", description="ID просматриваемой детали цены"),
    context=Depends(require_permission_in_context("view_price_detail")),
):
    logger.info(f"Запрос на просмотр деталь цены: {price_detail_id}")
    price_detail = await PriceDetail.filter(id=price_detail_id).first()

    if price_detail is None:
        logger.warning(f"деталь цен {price_detail_id} не найдена")
        raise HTTPException(status_code=404, detail="деталь цен не найдена")
    validate_company_access(price_detail, context, "деталь цен")
    price_detail_schema = PriceDetailSchema.model_validate(price_detail)

    logger.success(f"деталь цен найдена: {price_detail_schema}")
    return price_detail_schema
