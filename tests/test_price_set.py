import pytest
from httpx import AsyncClient

from app.database.models import PriceSet


@pytest.mark.asyncio
async def test_add_price_set(test_app: AsyncClient, jwt_token_admin: dict, seed_company):
    """Тест добавления нового набора цен."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {"price_set_name": "Test Price Set", "company_id": str(seed_company)}

    response = await test_app.post("/api/price-sets/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price_set = await PriceSet.filter(company_id=seed_company).first()

    assert price_set is not None, "Набор цен не был сохранён в БД"
    assert response_data["price_set_id"] == str(price_set.id)


@pytest.mark.asyncio
async def test_edit_price_set(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set: PriceSet):
    """Тест редактирования набора цен."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {"price_set_name": "Updated Price Set"}

    response = await test_app.patch(f"/api/price-sets/{seed_price_set.id}", headers=headers, json=data)
    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price_set = await PriceSet.filter(id=seed_price_set.id).first()
    assert price_set is not None, "Набор цен не найден в базе"
    assert price_set.name == "Updated Price Set"


@pytest.mark.asyncio
async def test_view_price_set(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set: PriceSet):
    """Тест просмотра набора цен по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/price-sets/{seed_price_set.id}", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["price_set_id"] == str(seed_price_set.id)


@pytest.mark.asyncio
async def test_delete_price_set(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set: PriceSet):
    """Тест удаления набора цен."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(f"/api/price-sets/{seed_price_set.id}", headers=headers)
    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price_set = await PriceSet.filter(id=seed_price_set.id).first()
    assert price_set is None, "Набор цен не был удалён из базы"


@pytest.mark.asyncio
async def test_get_price_sets(test_app: AsyncClient, jwt_token_admin: dict, seed_price_set: PriceSet):
    """Тест получения списка наборов цен с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/price-sets/all", headers=headers)
    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price_sets = response_data.get("price_sets")
    assert isinstance(price_sets, list), "Ответ должен быть списком"
    assert response_data.get("total") > 0

    price_set_ids = [ps["price_set_id"] for ps in price_sets]
    assert str(seed_price_set.id) in price_set_ids, "Тестовый набор цен отсутствует в списке"
