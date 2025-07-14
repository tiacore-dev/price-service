import pytest
from httpx import AsyncClient

from app.database.models import PriceCategory


@pytest.mark.asyncio
async def test_add_price_category(test_app: AsyncClient, jwt_token_admin: dict, seed_company):
    """Тест добавления нового промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {"price_category_name": "Test Price_category", "company_id": str(seed_company)}

    response = await test_app.post("/api/price-categories/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price_category = await PriceCategory.filter(company_id=seed_company).first()

    assert price_category is not None, "Промпт не был сохранён в БД"
    assert response_data["price_category_id"] == str(price_category.id)


@pytest.mark.asyncio
async def test_edit_price_category(test_app: AsyncClient, jwt_token_admin: dict, seed_price_category: PriceCategory):
    """Тест редактирования промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "price_category_name": "Updated Price_category",
    }

    response = await test_app.patch(f"/api/price-categories/{seed_price_category.id}", headers=headers, json=data)

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price_category = await PriceCategory.filter(id=seed_price_category.id).first()

    assert price_category is not None, "Промпт не найден в базе"


@pytest.mark.asyncio
async def test_view_price_category(test_app: AsyncClient, jwt_token_admin: dict, seed_price_category: PriceCategory):
    """Тест просмотра промпта по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/price-categories/{seed_price_category.id}", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["price_category_id"] == str(seed_price_category.id)


@pytest.mark.asyncio
async def test_delete_price_category(test_app: AsyncClient, jwt_token_admin: dict, seed_price_category: PriceCategory):
    """Тест удаления промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(f"/api/price-categories/{seed_price_category.id}", headers=headers)

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price_category = await PriceCategory.filter(id=seed_price_category.id).first()
    assert price_category is None, "Промпт не был удалён из базы"


@pytest.mark.asyncio
async def test_get_price_categories(test_app: AsyncClient, jwt_token_admin: dict, seed_price_category: PriceCategory):
    """Тест получения списка промптов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/price-categories/all", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price_categories = response_data.get("categories")
    print(price_categories)
    assert isinstance(price_categories, list), "Ответ должен быть списком"
    assert response_data.get("total") > 0

    price_category_ids = [price_category["price_category_id"] for price_category in price_categories]
    assert str(seed_price_category.id) in price_category_ids, "Тестовый промпт отсутствует в списке"
