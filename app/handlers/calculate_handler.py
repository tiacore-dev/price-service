from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, getcontext
from typing import Iterable, List
from uuid import UUID

from app.database.models import PriceDetail

getcontext().prec = 28


class PricingError(Exception): ...


class PriceRangeNotFound(PricingError): ...


class InvalidPriceDetail(PricingError): ...


@dataclass
class QuoteResult:
    total_amount: Decimal
    price_detail_id: UUID
    extra_increments: int


def _to_decimal(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def compute_quote_amount(
    base_value: Decimal,
    price_details: Iterable[PriceDetail],
    *,
    fallback_to_top_if_out_of_range: bool = True,
) -> QuoteResult:
    """
    Ищем price_detail с weight_from ≤ base_value ≤ weight_to.
    Если не нашли и fallback_to_top_if_out_of_range=True — берём верхний диапазон
    (последний по порядку), считаем по нему.
    Формулы:
      additional_weight = max(0, base_value - weight_from)
      extra_increments  = ceil(additional_weight / weight_extra)
      total_amount      = value_fix + value_extra * extra_increments
    """
    bval = _to_decimal(base_value)
    details: List[PriceDetail] = list(price_details)
    details.sort(key=lambda d: (_to_decimal(d.weight_from), _to_decimal(d.weight_to)))

    for d in details:
        wf = _to_decimal(d.weight_from)
        wt = _to_decimal(d.weight_to)
        inc = _to_decimal(d.weight_extra)
        fix = _to_decimal(d.value_fix)
        add = _to_decimal(d.value_extra)

        if inc <= 0:
            raise InvalidPriceDetail(f"weight_extra must be > 0 for PriceDetail {d.id}")

        if wf <= bval <= wt:
            extra = bval - wf
            if extra < 0:
                extra = Decimal("0")
            steps = int((extra / inc).to_integral_value(rounding=ROUND_CEILING))
            amount = (fix + add * steps).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return QuoteResult(total_amount=amount, price_detail_id=d.id, extra_increments=steps)

    if not details:
        raise PriceRangeNotFound("no price details")

    if fallback_to_top_if_out_of_range:
        # верхний диапазон — самый последний после сортировки
        d = details[-1]
        wf = _to_decimal(d.weight_from)
        inc = _to_decimal(d.weight_extra)
        fix = _to_decimal(d.value_fix)
        add = _to_decimal(d.value_extra)

        if inc <= 0:
            raise InvalidPriceDetail(f"weight_extra must be > 0 for PriceDetail {d.id}")

        extra = bval - wf
        if extra < 0:
            extra = Decimal("0")
        steps = int((extra / inc).to_integral_value(rounding=ROUND_CEILING))
        amount = (fix + add * steps).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return QuoteResult(total_amount=amount, price_detail_id=d.id, extra_increments=steps)

    # если fallback выключен — ведём себя по-старому
    raise PriceRangeNotFound("base_value вне диапазонов")
