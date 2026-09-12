from __future__ import annotations

from decimal import Decimal

import pandas as pd

from src.attribution import (
    attribute_orders,
    calculate_weights,
)
from src.romi import (
    calculate_romi_by_placement,
)


def orders() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_id": 1,
                "student_id": "42",
                "timestamp": pd.Timestamp(
                    "2026-09-10 12:00:00"
                ),
                "order_revenue": Decimal(
                    "9000.00"
                ),
            }
        ]
    )


def placements() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "placement_id": "pl_a",
                "campaign_id": "camp_a",
                "creative_id": "cr_a",
                "channel": "telegram",
                "publisher": "channel_a",
                "cost": Decimal(
                    "1000.00"
                ),
            },
            {
                "placement_id": "pl_b",
                "campaign_id": "camp_b",
                "creative_id": "cr_b",
                "channel": "telegram",
                "publisher": "channel_b",
                "cost": Decimal(
                    "1000.00"
                ),
            },
            {
                "placement_id": "pl_c",
                "campaign_id": "camp_c",
                "creative_id": "cr_c",
                "channel": "telegram",
                "publisher": "channel_c",
                "cost": Decimal(
                    "1000.00"
                ),
            },
        ]
    )


def touches() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "touch_id": "t_a",
                "placement_id": "pl_a",
                "user_id": "42",
                "event_type": "click",
                "occurred_at": pd.Timestamp(
                    "2026-09-01 12:00:00"
                ),
            },
            {
                "touch_id": "t_b",
                "placement_id": "pl_b",
                "user_id": "42",
                "event_type": "click",
                "occurred_at": pd.Timestamp(
                    "2026-09-05 12:00:00"
                ),
            },
            {
                "touch_id": "t_c",
                "placement_id": "pl_c",
                "user_id": "42",
                "event_type": "bot_start",
                "occurred_at": pd.Timestamp(
                    "2026-09-09 12:00:00"
                ),
            },
        ]
    )


def test_first_touch() -> None:
    result = attribute_orders(
        orders=orders(),
        touches=touches(),
        placements=placements(),
        model="first_touch",
        window_days=30,
    )

    assert len(result) == 1

    assert (
        result.iloc[0][
            "touch_id"
        ]
        == "t_a"
    )


def test_last_touch() -> None:
    result = attribute_orders(
        orders=orders(),
        touches=touches(),
        placements=placements(),
        model="last_touch",
        window_days=30,
    )

    assert (
        result.iloc[0][
            "touch_id"
        ]
        == "t_c"
    )


def test_linear() -> None:
    result = attribute_orders(
        orders=orders(),
        touches=touches(),
        placements=placements(),
        model="linear",
        window_days=30,
    )

    assert len(result) == 3

    assert (
        sum(
            result["weight"],
            Decimal("0"),
        )
        == Decimal("1")
    )

    assert (
        sum(
            result[
                "attributed_revenue"
            ],
            Decimal("0"),
        )
        == Decimal("9000.00")
    )


def test_window() -> None:
    source = touches()

    source.loc[
        source["touch_id"]
        == "t_a",
        "occurred_at",
    ] = pd.Timestamp(
        "2026-07-01 12:00:00"
    )

    result = attribute_orders(
        orders=orders(),
        touches=source,
        placements=placements(),
        model="first_touch",
        window_days=30,
    )

    assert (
        result.iloc[0][
            "touch_id"
        ]
        == "t_b"
    )


def test_time_decay() -> None:
    weights = calculate_weights(
        touches=touches(),
        model="time_decay",
        purchase_time=pd.Timestamp(
            "2026-09-10 12:00:00"
        ),
    )

    assert (
        weights[2]
        > weights[1]
        > weights[0]
    )

    assert (
        sum(
            weights,
            Decimal("0"),
        )
        == Decimal("1")
    )


def test_position_based() -> None:
    weights = calculate_weights(
        touches=touches(),
        model="position_based",
        purchase_time=pd.Timestamp(
            "2026-09-10 12:00:00"
        ),
    )

    assert weights == [
        Decimal(
            "0.400000000000"
        ),
        Decimal(
            "0.200000000000"
        ),
        Decimal(
            "0.400000000000"
        ),
    ]


def test_romi_cost_is_not_duplicated() -> None:
    attribution = pd.DataFrame(
        [
            {
                "model": "linear",
                "placement_id": "pl_a",
                "attributed_revenue": Decimal(
                    "3000.00"
                ),
            },
            {
                "model": "linear",
                "placement_id": "pl_a",
                "attributed_revenue": Decimal(
                    "2000.00"
                ),
            },
        ]
    )

    source_placements = (
        pd.DataFrame(
            [
                {
                    "placement_id": "pl_a",
                    "campaign_id": "camp_a",
                    "channel": "telegram",
                    "publisher": "channel_a",
                    "cost": Decimal(
                        "1000.00"
                    ),
                }
            ]
        )
    )

    result = (
        calculate_romi_by_placement(
            attribution=attribution,
            placements=(
                source_placements
            ),
            contribution_margin_rate=(
                Decimal("0.6")
            ),
        )
    )

    linear = result[
        result["model"]
        == "linear"
    ].iloc[0]

    assert (
        linear[
            "attributed_revenue"
        ]
        == Decimal("5000.00")
    )

    assert (
        linear["cost"]
        == Decimal("1000.00")
    )

    assert (
        linear["romi_attr"]
        == Decimal("4")
    )