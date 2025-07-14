from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "price_categories" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "company_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" UUID NOT NULL,
    "modified_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modified_by" UUID NOT NULL,
    "parent_id" UUID REFERENCES "price_categories" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "prices" (
    "id" UUID NOT NULL PRIMARY KEY,
    "company_id" UUID NOT NULL,
    "sender_city" UUID NOT NULL,
    "sender_warehouse" UUID,
    "recipient_city" UUID NOT NULL,
    "recipient_warehouse" UUID,
    "comment" TEXT,
    "delivery_duration" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" UUID NOT NULL,
    "modified_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modified_by" UUID NOT NULL,
    "price_category_id" UUID NOT NULL REFERENCES "price_categories" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "price_details" (
    "id" UUID NOT NULL PRIMARY KEY,
    "company_id" UUID NOT NULL,
    "weight_from" DECIMAL(10,3) NOT NULL,
    "weight_to" DECIMAL(10,3) NOT NULL,
    "weight_extra" DECIMAL(10,3) NOT NULL,
    "value_fix" DECIMAL(10,2) NOT NULL,
    "value_extra" DECIMAL(10,2) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" UUID NOT NULL,
    "modified_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modified_by" UUID NOT NULL,
    "price_id" UUID NOT NULL REFERENCES "prices" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "price_sets" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "company_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" UUID NOT NULL,
    "modified_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modified_by" UUID NOT NULL
);
CREATE TABLE IF NOT EXISTS "price_set_relations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "company_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" UUID NOT NULL,
    "modified_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modified_by" UUID NOT NULL,
    "price_id" UUID NOT NULL REFERENCES "prices" ("id") ON DELETE CASCADE,
    "price_set_id" UUID NOT NULL REFERENCES "price_sets" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
