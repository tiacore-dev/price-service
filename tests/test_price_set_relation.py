import pytest
from httpx import AsyncClient

from app.database.models import Price, PriceSet, PriceSetRelation


@pytest.mark.asyncio
async def test_add_price_set_relation(
    test_app: AsyncClient, jwt_token_admin: dict, seed_company, seed_price: Price, seed_price_set: PriceSet
):
    """Тест создания связи между ценой и набором цен."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    data = {
        "price_id": str(seed_price.id),
        "price_set_id": str(seed_price_set.id),
        "company_id": str(seed_company),
    }

    response = await test_app.post("/api/price-set-relations/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    relation = await PriceSetRelation.filter(company_id=seed_company).first()

    assert relation is not None, "Связь не была создана в БД"
    assert response_data["relation_id"] == str(relation.id)


@pytest.mark.asyncio
async def test_edit_price_set_relation(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set_relation):
    """Тест редактирования связи (например, смена набора цен)."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    from app.database.models import PriceSet

    new_price_set = await PriceSet.create(
        name="Updated Set",
        company_id=seed_price_set_relation.company_id,
        created_by=seed_price_set_relation.created_by,
        modified_by=seed_price_set_relation.modified_by,
    )

    data = {
        "price_set_id": str(new_price_set.id),
    }

    response = await test_app.patch(
        f"/api/price-set-relations/{seed_price_set_relation.id}", headers=headers, json=data
    )
    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    updated = await PriceSetRelation.filter(id=seed_price_set_relation.id).prefetch_related("price_set").first()
    if not updated:
        raise
    assert updated.price_set.id == new_price_set.id


@pytest.mark.asyncio
async def test_view_price_set_relation(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set_relation):
    """Тест получения связи по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/price-set-relations/{seed_price_set_relation.id}", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"
    assert response.json()["relation_id"] == str(seed_price_set_relation.id)


@pytest.mark.asyncio
async def test_delete_price_set_relation(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set_relation):
    """Тест удаления связи между ценой и набором."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(f"/api/price-set-relations/{seed_price_set_relation.id}", headers=headers)
    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    relation = await PriceSetRelation.filter(id=seed_price_set_relation.id).first()
    assert relation is None


@pytest.mark.asyncio
async def test_get_price_set_relations(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set_relation):
    """Тест списка связей."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/price-set-relations/all", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    relations = response_data.get("relations")
    assert isinstance(relations, list)
    assert response_data.get("total") > 0

    ids = [r["relation_id"] for r in relations]
    assert str(seed_price_set_relation.id) in ids
