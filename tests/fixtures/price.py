from uuid import uuid4

import pytest

from app.database.models import Price, PriceCategory, PriceDetail, PriceSet, PriceSetRelation


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_company():
    company_id = uuid4()
    return company_id


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_user():
    user_id = uuid4()
    return user_id


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_price_category(seed_company, seed_user):
    category = await PriceCategory.create(
        name="Test_category", company_id=seed_company, created_by=seed_user, modified_by=seed_user
    )
    return category


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_price(seed_company, seed_user, seed_price_category: PriceCategory):
    price = await Price.create(
        company_id=seed_company,
        created_by=seed_user,
        modified_by=seed_user,
        price_category=seed_price_category,
        sender_city=uuid4(),
        recipient_city=uuid4(),
        delivery_duration=2,
    )
    return price


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_price_detail(seed_company, seed_user, seed_price: Price):
    price = await PriceDetail.create(
        company_id=seed_company,
        created_by=seed_user,
        modified_by=seed_user,
        price=seed_price,
        weight_from=1,
        weight_to=2,
        weight_extra=1,
        value_fix=3,
        value_extra=4,
    )
    return price


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_price_set(seed_company, seed_user):
    price_set = await PriceSet.create(
        name="Test PriceSet",
        company_id=seed_company,
        created_by=seed_user,
        modified_by=seed_user,
    )
    return price_set


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def seed_price_set_relation(seed_company, seed_user, seed_price: Price, seed_price_set: PriceSet):
    # Создаём связь
    relation = await PriceSetRelation.create(
        price=seed_price,
        price_set=seed_price_set,
        company_id=seed_company,
        created_by=seed_user,
        modified_by=seed_user,
    )
    return relation
