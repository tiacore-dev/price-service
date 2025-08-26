import uuid
from enum import Enum

from tortoise import fields
from tortoise.models import Model


class ServiceType(str, Enum):
    STANDARD = "standard"  # Стандартная доставка
    EXPRESS = "express"  # Срочная доставка
    THERMAL = "thermal"  # Терморежим
    FRAGILE = "fragile"  # Хрупкий груз
    PERSONAL = "personal"  # Лично в руки

    @property
    def label(self) -> str:
        return {
            ServiceType.STANDARD: "Стандартная доставка",
            ServiceType.EXPRESS: "Срочная доставка",
            ServiceType.THERMAL: "Терморежим",
            ServiceType.FRAGILE: "Хрупкий груз",
            ServiceType.PERSONAL: "Лично в руки",
        }[self]


class PriceCategory(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    parent = fields.ForeignKeyField("models.PriceCategory", related_name="children", null=True)
    name = fields.CharField(max_length=100)
    company_id = fields.UUIDField()

    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.UUIDField()
    modified_at = fields.DatetimeField(auto_now=True)
    modified_by = fields.UUIDField()

    class Meta:
        table = "price_categories"


class Price(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    company_id = fields.UUIDField()
    price_category = fields.ForeignKeyField("models.PriceCategory", related_name="prices")
    sender_city = fields.UUIDField()
    sender_warehouse = fields.UUIDField(null=True)
    recipient_city = fields.UUIDField()
    recipient_warehouse = fields.UUIDField(null=True)
    comment = fields.TextField(null=True)
    delivery_duration = fields.IntField()
    service_type = fields.CharEnumField(ServiceType)

    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.UUIDField()
    modified_at = fields.DatetimeField(auto_now=True)
    modified_by = fields.UUIDField()

    class Meta:
        table = "prices"


class PriceDetail(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    price = fields.ForeignKeyField("models.Price", related_name="price_details")
    company_id = fields.UUIDField()
    # Вес с точностью до грамма: 3 знака после запятой
    weight_from = fields.DecimalField(max_digits=10, decimal_places=3)
    weight_to = fields.DecimalField(max_digits=10, decimal_places=3)
    weight_extra = fields.DecimalField(max_digits=10, decimal_places=3)
    # Стоимость с точностью до копеек: 2 знака после запятой
    value_fix = fields.DecimalField(max_digits=10, decimal_places=2)
    value_extra = fields.DecimalField(max_digits=10, decimal_places=2)

    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.UUIDField()
    modified_at = fields.DatetimeField(auto_now=True)
    modified_by = fields.UUIDField()

    class Meta:
        table = "price_details"


class PriceSet(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=100)
    company_id = fields.UUIDField()

    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.UUIDField()
    modified_at = fields.DatetimeField(auto_now=True)
    modified_by = fields.UUIDField()

    class Meta:
        table = "price_sets"


class PriceSetRelation(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    price = fields.ForeignKeyField("models.Price", related_name="price_set_relations")
    price_set = fields.ForeignKeyField("models.PriceSet", related_name="price_set_relations")
    company_id = fields.UUIDField()

    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.UUIDField()
    modified_at = fields.DatetimeField(auto_now=True)
    modified_by = fields.UUIDField()

    class Meta:
        table = "price_set_relations"
