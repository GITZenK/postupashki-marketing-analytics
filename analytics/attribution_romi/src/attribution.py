from __future__ import annotations

import math
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from src.config import (
    DEFAULT_ATTRIBUTION_WINDOW_DAYS,
    POSITION_BASED_FIRST_WEIGHT,
    POSITION_BASED_LAST_WEIGHT,
    TIME_DECAY_HALF_LIFE_DAYS,
)


SUPPORTED_MODELS = (
    "first_touch",
    "last_touch",
    "linear",
    "time_decay",
    "position_based",
)

MONEY_QUANT = Decimal("0.01")

WEIGHT_QUANT = Decimal(
    "0.000000000001"
)


def _normalize_weights(
    weights: list[Decimal],
) -> list[Decimal]:
    total = sum(
        weights,
        Decimal("0"),
    )

    if total <= 0:
        raise ValueError(
            "Attribution weights must "
            "have a positive sum"
        )

    normalized = [
        (
            weight / total
        ).quantize(
            WEIGHT_QUANT
        )
        for weight in weights
    ]

    residual = (
        Decimal("1")
        - sum(
            normalized,
            Decimal("0"),
        )
    )

    normalized[-1] += residual

    return normalized


def _linear_weights(
    n_touches: int,
) -> list[Decimal]:
    return _normalize_weights(
        [
            Decimal("1")
            for _ in range(
                n_touches
            )
        ]
    )


def _time_decay_weights(
    touches: pd.DataFrame,
    purchase_time: pd.Timestamp,
) -> list[Decimal]:
    weights: list[Decimal] = []

    for touch_time in touches[
        "occurred_at"
    ]:
        age_days = max(
            0.0,
            (
                purchase_time
                - touch_time
            ).total_seconds()
            / 86400,
        )

        score = math.pow(
            0.5,
            age_days
            / TIME_DECAY_HALF_LIFE_DAYS,
        )

        weights.append(
            Decimal(str(score))
        )

    return _normalize_weights(
        weights
    )


def _position_based_weights(
    n_touches: int,
) -> list[Decimal]:
    if n_touches == 1:
        return [
            Decimal("1")
        ]

    if n_touches == 2:
        return [
            Decimal("0.5"),
            Decimal("0.5"),
        ]

    middle_total = (
        Decimal("1")
        - POSITION_BASED_FIRST_WEIGHT
        - POSITION_BASED_LAST_WEIGHT
    )

    middle_weight = (
        middle_total
        / Decimal(
            n_touches - 2
        )
    )

    return [
        POSITION_BASED_FIRST_WEIGHT,
        *[
            middle_weight
            for _ in range(
                n_touches - 2
            )
        ],
        POSITION_BASED_LAST_WEIGHT,
    ]


def calculate_weights(
    touches: pd.DataFrame,
    model: str,
    purchase_time: pd.Timestamp,
) -> list[Decimal]:
    n_touches = len(touches)

    if n_touches == 0:
        return []

    if model in {
        "first_touch",
        "last_touch",
    }:
        return [
            Decimal("1")
        ]

    if model == "linear":
        return _linear_weights(
            n_touches
        )

    if model == "time_decay":
        return _time_decay_weights(
            touches=touches,
            purchase_time=(
                purchase_time
            ),
        )

    if model == "position_based":
        return _normalize_weights(
            _position_based_weights(
                n_touches
            )
        )

    raise ValueError(
        f"Unknown attribution model: "
        f"{model}"
    )


def _eligible_touches(
    touches: pd.DataFrame,
    user_id: str,
    purchase_time: pd.Timestamp,
    window_days: int,
) -> pd.DataFrame:
    window_start = (
        purchase_time
        - timedelta(
            days=window_days
        )
    )

    mask = (
        (
            touches["user_id"]
            .astype(str)
            == str(user_id)
        )
        & (
            touches["occurred_at"]
            <= purchase_time
        )
        & (
            touches["occurred_at"]
            >= window_start
        )
    )

    return (
        touches.loc[mask]
        .sort_values(
            "occurred_at"
        )
        .reset_index(
            drop=True
        )
    )


def _allocate_revenue(
    revenue: Decimal,
    weights: list[Decimal],
) -> list[Decimal]:
    if not weights:
        return []

    values: list[Decimal] = []

    assigned = Decimal("0")

    for weight in weights[:-1]:
        value = (
            revenue * weight
        ).quantize(
            MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )

        values.append(value)
        assigned += value

    final_value = (
        revenue - assigned
    ).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )

    values.append(
        final_value
    )

    return values


def attribute_orders(
    orders: pd.DataFrame,
    touches: pd.DataFrame,
    placements: pd.DataFrame,
    model: str,
    window_days: int = DEFAULT_ATTRIBUTION_WINDOW_DAYS,
) -> pd.DataFrame:
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unknown attribution model: "
            f"{model}"
        )

    if window_days <= 0:
        raise ValueError(
            "Attribution window "
            "must be positive"
        )

    placement_lookup = (
        placements[
            [
                "placement_id",
                "campaign_id",
                "creative_id",
                "channel",
                "publisher",
            ]
        ]
        .set_index(
            "placement_id"
        )
    )

    rows: list[
        dict[str, object]
    ] = []

    for order in orders.itertuples(
        index=False
    ):
        eligible = _eligible_touches(
            touches=touches,
            user_id=str(
                order.student_id
            ),
            purchase_time=(
                order.timestamp
            ),
            window_days=window_days,
        )

        if eligible.empty:
            continue

        if model == "first_touch":
            selected = eligible.iloc[
                [0]
            ].copy()

        elif model == "last_touch":
            selected = eligible.iloc[
                [-1]
            ].copy()

        else:
            selected = eligible.copy()

        weights = calculate_weights(
            touches=selected,
            model=model,
            purchase_time=(
                order.timestamp
            ),
        )

        revenue = Decimal(
            str(
                order.order_revenue
            )
        ).quantize(
            MONEY_QUANT
        )

        revenue_parts = (
            _allocate_revenue(
                revenue=revenue,
                weights=weights,
            )
        )

        for (
            touch,
            weight,
            revenue_part,
        ) in zip(
            selected.itertuples(
                index=False
            ),
            weights,
            revenue_parts,
        ):
            placement = (
                placement_lookup.loc[
                    touch.placement_id
                ]
            )

            rows.append(
                {
                    "order_id": int(
                        order.order_id
                    ),
                    "user_id": str(
                        order.student_id
                    ),
                    "touch_id": (
                        touch.touch_id
                    ),
                    "placement_id": (
                        touch.placement_id
                    ),
                    "campaign_id": (
                        placement[
                            "campaign_id"
                        ]
                    ),
                    "creative_id": (
                        placement[
                            "creative_id"
                        ]
                    ),
                    "channel": (
                        placement[
                            "channel"
                        ]
                    ),
                    "publisher": (
                        placement[
                            "publisher"
                        ]
                    ),
                    "event_type": (
                        touch.event_type
                    ),
                    "model": model,
                    "weight": weight,
                    "order_revenue": (
                        revenue
                    ),
                    "attributed_revenue": (
                        revenue_part
                    ),
                    "touch_time": (
                        touch.occurred_at
                    ),
                    "purchase_time": (
                        order.timestamp
                    ),
                    "attribution_window_days": (
                        window_days
                    ),
                }
            )

    return pd.DataFrame(rows)


def validate_attribution(
    attribution: pd.DataFrame,
) -> None:
    if attribution.empty:
        return

    grouped = attribution.groupby(
        [
            "order_id",
            "model",
        ]
    )

    for _, group in grouped:
        weight_sum = sum(
            group["weight"],
            Decimal("0"),
        )

        revenue_sum = sum(
            group[
                "attributed_revenue"
            ],
            Decimal("0"),
        )

        order_revenue = Decimal(
            str(
                group[
                    "order_revenue"
                ].iloc[0]
            )
        ).quantize(
            MONEY_QUANT
        )

        if (
            abs(
                weight_sum
                - Decimal("1")
            )
            > Decimal(
                "0.000000001"
            )
        ):
            raise ValueError(
                "Attribution weights "
                "do not sum to 1"
            )

        if (
            revenue_sum
            != order_revenue
        ):
            raise ValueError(
                "Attributed revenue "
                "does not equal "
                "order revenue"
            )


def attribute_all_models(
    orders: pd.DataFrame,
    touches: pd.DataFrame,
    placements: pd.DataFrame,
    window_days: int = DEFAULT_ATTRIBUTION_WINDOW_DAYS,
) -> pd.DataFrame:
    frames: list[
        pd.DataFrame
    ] = []

    for model in SUPPORTED_MODELS:
        result = attribute_orders(
            orders=orders,
            touches=touches,
            placements=placements,
            model=model,
            window_days=window_days,
        )

        if not result.empty:
            frames.append(result)

    if not frames:
        return pd.DataFrame()

    attribution = pd.concat(
        frames,
        ignore_index=True,
    )

    validate_attribution(
        attribution
    )

    return attribution


def build_attribution_coverage(
    orders: pd.DataFrame,
    attribution: pd.DataFrame,
) -> pd.DataFrame:
    total_orders = len(orders)

    total_revenue = sum(
        (
            Decimal(str(value))
            for value
            in orders[
                "order_revenue"
            ]
        ),
        Decimal("0"),
    )

    rows: list[
        dict[str, object]
    ] = []

    for model in SUPPORTED_MODELS:
        model_data = attribution[
            attribution["model"]
            == model
        ]

        attributed_ids = set(
            model_data[
                "order_id"
            ].unique()
        )

        attributed_orders = len(
            attributed_ids
        )

        attributed_revenue = sum(
            (
                Decimal(str(value))
                for value
                in orders.loc[
                    orders[
                        "order_id"
                    ].isin(
                        attributed_ids
                    ),
                    "order_revenue",
                ]
            ),
            Decimal("0"),
        )

        rows.append(
            {
                "model": model,
                "total_orders": (
                    total_orders
                ),
                "attributed_orders": (
                    attributed_orders
                ),
                "unattributed_orders": (
                    total_orders
                    - attributed_orders
                ),
                "order_coverage": (
                    attributed_orders
                    / total_orders
                    if total_orders
                    else 0.0
                ),
                "total_revenue": (
                    total_revenue
                ),
                "attributed_order_revenue": (
                    attributed_revenue
                ),
                "revenue_coverage": (
                    float(
                        attributed_revenue
                        / total_revenue
                    )
                    if total_revenue
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(rows)