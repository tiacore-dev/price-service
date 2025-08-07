from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.handlers.permissions_handler import with_permission_and_company_from_body_check
from tiacore_lib.utils.validate_helpers import validate_company_access, validate_exists
from tortoise.expressions import Q

from app.database.models import Price, PriceSet, PriceSetRelation
from app.pydantic_models.price_set_relation_models import (
    PriceSetRelationCreateSchema,
    PriceSetRelationEditSchema,
    PriceSetRelationListResponseSchema,
    PriceSetRelationResponseSchema,
    PriceSetRelationSchema,
    price_set_relation_filter_params,
)

price_set_relation_router = APIRouter()


@price_set_relation_router.post(
    "/add",
    response_model=PriceSetRelationResponseSchema,
    summary="Добавление новой связи цены и набора цен",
    status_code=status.HTTP_201_CREATED,
)
async def add_price_set_relation(
    data: PriceSetRelationCreateSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("add_price_set_relation")),
):
    await validate_exists(Price, data.price_id, "Цена")
    await validate_exists(PriceSet, data.price_set_id, "Набор цен")
    relation = await PriceSetRelation.create(
        created_by=context["user_id"],
        modified_by=context["user_id"],
        **data.model_dump(exclude_unset=True),
    )
    if not relation:
        logger.error("Не удалось создать связь цены и набора")
        raise HTTPException(status_code=500, detail="Не удалось создать связь")

    logger.success(f"Связь {relation.id} успешно создана")
    return PriceSetRelationResponseSchema(relation_id=relation.id)


@price_set_relation_router.patch(
    "/{relation_id}",
    summary="Изменение связи цены и набора",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def edit_price_set_relation(
    relation_id: UUID = Path(..., title="ID связи", description="ID редактируемой связи"),
    data: PriceSetRelationEditSchema = Body(...),
    context=Depends(with_permission_and_company_from_body_check("edit_price_set_relation")),
):
    logger.info(f"Обновление связи {relation_id}")
    relation = await PriceSetRelation.filter(id=relation_id).first()

    if not relation:
        logger.warning(f"Связь {relation_id} не найдена")
        raise HTTPException(status_code=404, detail="Связь не найдена")

    validate_company_access(relation, context, "связь цены и набора")
    if data.price_id:
        await validate_exists(Price, data.price_id, "Цена")
    if data.price_set_id:
        await validate_exists(PriceSet, data.price_set_id, "Набор цен")
    relation.modified_by = context["user_id"]
    await relation.update_from_dict(data.model_dump(exclude_unset=True))
    await relation.save()


@price_set_relation_router.delete(
    "/{relation_id}",
    summary="Удаление связи цены и набора",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_price_set_relation(
    relation_id: UUID = Path(..., title="ID связи", description="ID удаляемой связи"),
    context=Depends(require_permission_in_context("delete_price_set_relation")),
):
    relation = await PriceSetRelation.filter(id=relation_id).first()
    if not relation:
        logger.warning(f"Связь {relation_id} не найдена")
        raise HTTPException(status_code=404, detail="Связь не найдена")

    validate_company_access(relation, context, "связь цены и набора")
    await relation.delete()


@price_set_relation_router.get(
    "/all",
    response_model=PriceSetRelationListResponseSchema,
    summary="Получение списка связей с фильтрацией",
)
async def get_price_set_relations(
    filters: dict = Depends(price_set_relation_filter_params),
    context=Depends(require_permission_in_context("get_all_price_set_relations")),
):
    query = Q()

    if filters.get("price_id"):
        query &= Q(price_id=filters["price_id"])
    if filters.get("price_set_id"):
        query &= Q(price_set_id=filters["price_set_id"])
    if filters.get("company_id"):
        query &= Q(company_id=filters["company_id"])

    sort_by = filters.get("sort_by", "created_at")
    order_by = f"{'-' if filters.get('order') == 'desc' else ''}{sort_by}"
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 10)

    total_count = await PriceSetRelation.filter(query).count()
    relations = (
        await PriceSetRelation.filter(query)
        .order_by(order_by)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .prefetch_related("price")
    )

    return PriceSetRelationListResponseSchema(
        total=total_count,
        relations=[PriceSetRelationSchema.model_validate(relation, from_attributes=True) for relation in relations],
    )


@price_set_relation_router.get(
    "/{relation_id}",
    response_model=PriceSetRelationSchema,
    summary="Просмотр связи цены и набора",
)
async def get_price_set_relation(
    relation_id: UUID = Path(..., title="ID связи", description="ID просматриваемой связи"),
    context=Depends(require_permission_in_context("view_price_set_relation")),
):
    logger.info(f"Запрос на просмотр связи: {relation_id}")
    relation = await PriceSetRelation.filter(id=relation_id).prefetch_related("price").first()

    if relation is None:
        logger.warning(f"Связь {relation_id} не найдена")
        raise HTTPException(status_code=404, detail="Связь не найдена")

    validate_company_access(relation, context, "связь цены и набора")
    schema = PriceSetRelationSchema.model_validate(relation)
    logger.success(f"Связь найдена: {schema}")
    return schema
