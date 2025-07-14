from fastapi import FastAPI
from tiacore_lib.routes.company_route import company_router
from tiacore_lib.routes.user_route import user_router

from .price_category_route import price_category_router
from .price_detail_route import price_detail_router
from .price_route import price_router
from .price_set_relation_route import price_set_relation_router
from .price_set_route import price_set_router


def register_routes(app: FastAPI):
    app.include_router(user_router, prefix="/api/users", tags=["Users"])
    app.include_router(company_router, prefix="/api/companies", tags=["Companies"])

    app.include_router(price_category_router, prefix="/api/price-categories", tags=["PriceCategories"])
    app.include_router(price_router, prefix="/api/prices", tags=["Prices"])
    app.include_router(price_detail_router, prefix="/api/price-details", tags=["PriceDetails"])
    app.include_router(price_set_router, prefix="/api/price-sets", tags=["PriceSets"])
    app.include_router(price_set_relation_router, prefix="/api/price-set-relations", tags=["PriceSetRelations"])
