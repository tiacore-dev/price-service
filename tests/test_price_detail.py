import pytest
from httpx import AsyncClient

from app.database.models import Price, PriceDetail


@pytest.mark.asyncio
async def test_add_price_detail(test_app: AsyncClient, jwt_token_admin: dict, seed_company, seed_price: Price):
    """Тест добавления нового промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {
        "company_id": str(seed_company),
        "price_id": str(seed_price.id),
        "weight_from": 1,
        "weight_to": 2,
        "weight_extra": 1,
        "value_fix": 3,
        "value_extra": 4,
    }

    response = await test_app.post("/api/price-details/add", headers=headers, json=data)
    assert response.status_code == 201, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price_detail = await PriceDetail.filter(company_id=seed_company).first()

    assert price_detail is not None, "Промпт не был сохранён в БД"
    assert response_data["price_detail_id"] == str(price_detail.id)


@pytest.mark.asyncio
async def test_edit_price_detail(test_app: AsyncClient, jwt_token_admin: dict, seed_price_detail: PriceDetail):
    """Тест редактирования промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}
    data = {"weight_to": 3.0}

    response = await test_app.patch(f"/api/price-details/{seed_price_detail.id}", headers=headers, json=data)

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price_detail = await PriceDetail.filter(id=seed_price_detail.id).first()

    assert price_detail is not None, "Промпт не найден в базе"


@pytest.mark.asyncio
async def test_view_price_detail(test_app: AsyncClient, jwt_token_admin: dict, seed_price_detail: PriceDetail):
    """Тест просмотра промпта по ID."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get(f"/api/price-details/{seed_price_detail.id}", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    assert response_data["price_detail_id"] == str(seed_price_detail.id)


@pytest.mark.asyncio
async def test_delete_price_detail(test_app: AsyncClient, jwt_token_admin: dict, seed_price_detail: PriceDetail):
    """Тест удаления промпта."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.delete(f"/api/price-details/{seed_price_detail.id}", headers=headers)

    assert response.status_code == 204, f"Ошибка: {response.status_code}, {response.text}"

    price_detail = await PriceDetail.filter(id=seed_price_detail.id).first()
    assert price_detail is None, "Промпт не был удалён из базы"


@pytest.mark.asyncio
async def test_get_price_details(test_app: AsyncClient, jwt_token_admin: dict, seed_price_detail: PriceDetail):
    """Тест получения списка промптов с фильтрацией."""
    headers = {"Authorization": f"Bearer {jwt_token_admin['access_token']}"}

    response = await test_app.get("/api/price-details/all", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.status_code}, {response.text}"

    response_data = response.json()
    price_details = response_data.get("details")
    print(price_details)
    assert isinstance(price_details, list), "Ответ должен быть списком"
    assert response_data.get("total") > 0

    price_detail_ids = [price_detail["price_detail_id"] for price_detail in price_details]
    assert str(seed_price_detail.id) in price_detail_ids, "Тестовый промпт отсутствует в списке"
