from uuid import UUID

from tortoise.expressions import Q

from app.database.models import Price, ServiceType


async def get_price_id(
    price_set_id: UUID,
    sender_city_id: UUID,
    recipient_city_id: UUID,
    sender_warehouse_id: UUID | None,
    recipient_warehouse_id: UUID | None,
    service_type: ServiceType,
) -> UUID | None:
    qs = Price.filter(
        price_set_relations__price_set_id=price_set_id,
        sender_city=sender_city_id,
        recipient_city=recipient_city_id,
        service_type=service_type,
    )

    # склады: сначала точное совпадение, иначе запись с NULL
    if sender_warehouse_id is not None:
        qs = qs.filter(Q(sender_warehouse=sender_warehouse_id) | Q(sender_warehouse__isnull=True))
    else:
        qs = qs.filter(Q(sender_warehouse__isnull=True))

    if recipient_warehouse_id is not None:
        qs = qs.filter(Q(recipient_warehouse=recipient_warehouse_id) | Q(recipient_warehouse__isnull=True))
    else:
        qs = qs.filter(Q(recipient_warehouse__isnull=True))

    # при таком фильтре допускаются только (= указанному складу) ИЛИ NULL,
    # поэтому сортировка поднимет точные совпадения выше NULL
    price = await qs.order_by("sender_warehouse", "recipient_warehouse").first()
    if not price:
        return None
    return price.id
