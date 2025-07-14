from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.database.models import Price, PriceCategory


@pytest.mark.asyncio
async def test_add_price(
    test_app: AsyncClient, jwt_token_admin: dict, seed_company, seed_price_category: PriceCategory
):
    """Тест добавления нового промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "company_id": str(seed_company),
        "price_category_id": str(seed_price_category.id),
        "sender_city": str(uuid4()),
        "recipient_city": str(uuid4()),
        "delivery_duration": 2,
    }

    response = await test_app.post("/api/prices/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price = await Price.filter(company_id=seed_company).first()

    assert price is not None, "Промпт не был сохранён в БД"
    assert response_data["price_id"] == str(price.id)


@pytest.mark.asyncio
async def test_edit_price(test_app: AsyncClient, jwt_token_admin: dict, seed_price: Price):
    """Тест редактирования промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "price_name": "Updated Price",
    }

    response = await test_app.patch(f"/api/prices/{seed_price.id}", headers=headers, json=data)

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price = await Price.filter(id=seed_price.id).first()

    assert price is not None, "Промпт не найден в базе"


@pytest.mark.asyncio
async def test_view_price(test_app: AsyncClient, jwt_token_admin: dict, seed_price: Price):
    """Тест просмотра промпта по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/prices/{seed_price.id}", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["price_id"] == str(seed_price.id)


@pytest.mark.asyncio
async def test_delete_price(test_app: AsyncClient, jwt_token_admin: dict, seed_price: Price):
    """Тест удаления промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(f"/api/prices/{seed_price.id}", headers=headers)

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price = await Price.filter(id=seed_price.id).first()
    assert price is None, "Промпт не был удалён из базы"


@pytest.mark.asyncio
async def test_get_prices(test_app: AsyncClient, jwt_token_admin: dict, seed_price: Price):
    """Тест получения списка промптов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/prices/all", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    prices = response_data.get("prices")

    assert isinstance(prices, list), "Ответ должен быть списком"
    assert response_data.get("total") > 0

    price_ids = [price["price_id"] for price in prices]
    assert str(seed_price.id) in price_ids, "Тестовый промпт отсутствует в списке"
