from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, getcontext
from typing import Iterable
from uuid import UUID

from app.database.models import PriceDetail  # Tortoise ORM

getcontext().prec = 28  # достаточная точность для ден. арифметики


class PricingError(Exception): ...


class PriceRangeNotFound(PricingError): ...


class InvalidPriceDetail(PricingError): ...


@dataclass
class QuoteResult:
    total_amount: Decimal  # конечная сумма
    price_detail_id: UUID  # какой диапазон сработал
    extra_increments: int  # сколько "добавочных шагов" применили


def _to_decimal(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def compute_quote_amount(
    base_value: Decimal,
    price_details: Iterable[PriceDetail],
) -> QuoteResult:
    """
    Алгоритм:
      1) Идём по price_details (отсортировано по weight_from).
      2) Ищем detail, где weight_from ≤ base_value ≤ weight_to.
      3) additional_weight = max(0, base_value - weight_from).
      4) extra_increments = ceil(additional_weight / weight_increment).
      5) total_amount = fixed_price + extra_price * extra_increments.
    Все суммы считаем в Decimal, округляем до 0.01.
    """
    bval = _to_decimal(base_value)

    for detail in price_details:
        weight_from = _to_decimal(detail.weight_from)
        weight_to = _to_decimal(detail.weight_to)
        weight_increment = _to_decimal(detail.weight_extra)
        fixed_price = _to_decimal(detail.value_fix)
        extra_price = _to_decimal(detail.value_extra)

        if weight_increment <= 0:
            raise InvalidPriceDetail(f"weight_extra must be > 0 for PriceDetail {detail.id}")

        # попадает ли base_value в этот диапазон
        if not (weight_from <= bval <= weight_to):
            continue

        additional_weight = bval - weight_from
        if additional_weight < 0:
            additional_weight = Decimal("0")

        extra_increments = int((additional_weight / weight_increment).to_integral_value(rounding=ROUND_CEILING))
        total_amount = (fixed_price + extra_price * extra_increments).quantize(Decimal("0.01"))

        return QuoteResult(
            total_amount=total_amount,
            price_detail_id=detail.id,
            extra_increments=extra_increments,
        )

    raise PriceRangeNotFound(f"base_value {bval} не попадает ни в один диапазон")
