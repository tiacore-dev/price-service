from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.handlers.permissions_handler import (
    with_permission_and_company_from_body_check,
)
from tiacore_lib.utils.validate_helpers import validate_company_access, validate_exists
from tortoise.expressions import Q

from app.database.models import PriceCategory
from app.pydantic_models.price_category_models import (
    PriceCategoryCreateSchema,
    PriceCategoryEditSchema,
    PriceCategoryListResponseSchema,
    PriceCategoryResponseSchema,
    PriceCategorySchema,
    price_category_filter_params,
)

price_category_router = APIRouter()


@price_category_router.post(
    "/add",
    response_model=PriceCategoryResponseSchema,
    summary="Добавление новой категории цен",
    status_code=status.HTTP_201_CREATED,
)
async def add_price_category(
    data: PriceCategoryCreateSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("add_price_category")),
):
    if data.parent_id:
        await validate_exists(PriceCategory, data.parent_id, "Категория цен")
    price_category = await PriceCategory.create(
        created_by=context["user_id"],
        modified_by=context["user_id"],
        **data.model_dump(exclude_unset=True),
    )
    if not price_category:
        logger.error("Не удалось создать категорию цен")
        raise HTTPException(status_code=500, detail="Не удалось создать категорию цен")

    logger.success(f"категория цен {price_category.name} ({price_category.id}) успешно создан")
    return PriceCategoryResponseSchema(price_category_id=price_category.id)


@price_category_router.patch(
    "/{price_category_id}",
    summary="Изменение категории цен",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def edit_price_category(
    price_category_id: UUID = Path(..., title="ID категории цен", description="ID изменяемой категории цен"),
    data: PriceCategoryEditSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("edit_price_category")),
):
    logger.info(f"Обновление категории цен {price_category_id}")

    price_category = await PriceCategory.filter(id=price_category_id).first()
    if not price_category:
        logger.warning(f"категория цен {price_category_id} не найдена")
        raise HTTPException(status_code=404, detail="Категория цен не найдена")
    if data.parent_id:
        await validate_exists(PriceCategory, data.parent_id, "Категория цен")
    validate_company_access(price_category, context, "категорию ценом")
    price_category.modified_by = context["user_id"]
    await price_category.update_from_dict(data.model_dump(exclude_unset=True))
    await price_category.save()


@price_category_router.delete(
    "/{price_category_id}",
    summary="Удаление категории цен",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_price_category(
    price_category_id: UUID = Path(..., title="ID категории цен", description="ID удаляемой категории цен"),
    context=Depends(require_permission_in_context("delete_price_category")),
):
    price_category = await PriceCategory.filter(id=price_category_id).first()
    if not price_category:
        logger.warning(f"категория цен {price_category_id} не найдена")
        raise HTTPException(status_code=404, detail="категория цен не найдена")
    validate_company_access(price_category, context, "категория цен")
    await price_category.delete()


@price_category_router.get(
    "/all",
    response_model=PriceCategoryListResponseSchema,
    summary="Получение списка категорию ценов с фильтрацией",
)
async def get_price_categorys(
    filters: dict = Depends(price_category_filter_params),
    context=Depends(require_permission_in_context("get_all_price_categories")),
):
    query = Q()

    if filters.get("company_id"):
        query &= Q(company_id=filters.get("company_id"))
    if filters.get("price_category_name"):
        query &= Q(name__icontains=filters["price_category_name"])
    if filters.get("parent_id"):
        query &= Q(parent_id=filters["parent_id"])

    sort_by = filters.get("sort_by", "created_at")
    if sort_by == "price_category_name":
        sort_by = "name"
    order_by = f"{'-' if filters.get('order') == 'desc' else ''}{sort_by}"
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 10)

    total_count = await PriceCategory.filter(query).count()

    price_categories = (
        await PriceCategory.filter(query).order_by(order_by).offset((page - 1) * page_size).limit(page_size)
    )

    return PriceCategoryListResponseSchema(
        total=total_count,
        categories=[PriceCategorySchema.model_validate(price_category) for price_category in price_categories],
    )


@price_category_router.get(
    "/{price_category_id}", response_model=PriceCategorySchema, summary="Просмотр категории цены"
)
async def get_price_category(
    price_category_id: UUID = Path(..., title="ID категории цены", description="ID просматриваемой категории цены"),
    context=Depends(require_permission_in_context("view_price_category")),
):
    logger.info(f"Запрос на просмотр категорию цены: {price_category_id}")
    price_category = await PriceCategory.filter(id=price_category_id).first()

    if price_category is None:
        logger.warning(f"категория цен {price_category_id} не найдена")
        raise HTTPException(status_code=404, detail="категория цен не найдена")
    validate_company_access(price_category, context, "категория цен")
    price_category_schema = PriceCategorySchema.model_validate(price_category)

    logger.success(f"категория цен найдена: {price_category_schema}")
    return price_category_schema
