from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

import pandas as pd

from src.config import (
    MOCK_MAX_TOUCHES,
    MOCK_MIN_TOUCHES,
    MOCK_ORGANIC_SHARE,
    MOCK_RANDOM_SEED,
)


def build_mock_placements() -> pd.DataFrame:
    rows = [
        {
            "placement_id": "pl_tg_001",
            "campaign_id": "camp_aug_awareness",
            "creative_id": "cr_001",
            "channel": "telegram",
            "publisher": "tg_channel_a",
            "publication_at": "2026-08-01 10:00:00",
            "cost": Decimal("18000.00"),
            "tracking_token": "tg_aug_a_001",
        },
        {
            "placement_id": "pl_tg_002",
            "campaign_id": "camp_aug_awareness",
            "creative_id": "cr_002",
            "channel": "telegram",
            "publisher": "tg_channel_b",
            "publication_at": "2026-08-05 12:00:00",
            "cost": Decimal("22000.00"),
            "tracking_token": "tg_aug_b_002",
        },
        {
            "placement_id": "pl_tg_003",
            "campaign_id": "camp_aug_conversion",
            "creative_id": "cr_003",
            "channel": "telegram",
            "publisher": "tg_channel_c",
            "publication_at": "2026-08-12 11:00:00",
            "cost": Decimal("25000.00"),
            "tracking_token": "tg_aug_c_003",
        },
        {
            "placement_id": "pl_tg_004",
            "campaign_id": "camp_aug_conversion",
            "creative_id": "cr_004",
            "channel": "telegram",
            "publisher": "tg_channel_d",
            "publication_at": "2026-08-20 16:00:00",
            "cost": Decimal("30000.00"),
            "tracking_token": "tg_aug_d_004",
        },
        {
            "placement_id": "pl_tg_005",
            "campaign_id": "camp_sep_launch",
            "creative_id": "cr_005",
            "channel": "telegram",
            "publisher": "tg_channel_e",
            "publication_at": "2026-08-28 10:00:00",
            "cost": Decimal("28000.00"),
            "tracking_token": "tg_sep_e_005",
        },
        {
            "placement_id": "pl_tg_006",
            "campaign_id": "camp_sep_launch",
            "creative_id": "cr_006",
            "channel": "telegram",
            "publisher": "tg_channel_f",
            "publication_at": "2026-09-02 10:00:00",
            "cost": Decimal("32000.00"),
            "tracking_token": "tg_sep_f_006",
        },
    ]

    frame = pd.DataFrame(rows)

    frame["publication_at"] = pd.to_datetime(
        frame["publication_at"]
    )

    return frame


def _random_touch_time(
    publication_at: pd.Timestamp,
    purchase_at: pd.Timestamp,
    rng: random.Random,
) -> pd.Timestamp:
    start = publication_at + timedelta(
        hours=1
    )

    end = purchase_at - timedelta(
        hours=1
    )

    if start >= end:
        return start

    seconds = int(
        (
            end - start
        ).total_seconds()
    )

    offset = rng.randint(
        0,
        seconds,
    )

    return start + timedelta(
        seconds=offset
    )


def build_mock_touches(
    orders: pd.DataFrame,
    placements: pd.DataFrame,
) -> pd.DataFrame:
    rng = random.Random(
        MOCK_RANDOM_SEED
    )

    event_types = (
        "view",
        "click",
        "bot_start",
    )

    rows: list[
        dict[str, object]
    ] = []

    touch_number = 1

    orders = orders.sort_values(
        "timestamp"
    )

    for order in orders.itertuples(
        index=False
    ):
        if (
            rng.random()
            < MOCK_ORGANIC_SHARE
        ):
            continue

        available = placements[
            placements["publication_at"]
            <= order.timestamp - timedelta(hours=2)
        ]

        if available.empty:
            continue

        n_touches = rng.randint(
            MOCK_MIN_TOUCHES,
            MOCK_MAX_TOUCHES,
        )

        n_touches = min(
            n_touches,
            len(available),
        )

        selected_indices = rng.sample(
            list(available.index),
            k=n_touches,
        )

        selected = available.loc[
            selected_indices
        ]

        for placement in selected.itertuples(
            index=False
        ):
            occurred_at = _random_touch_time(
                publication_at=(
                    placement.publication_at
                ),
                purchase_at=order.timestamp,
                rng=rng,
            )

            rows.append(
                {
                    "touch_id": (
                        f"touch_{touch_number:05d}"
                    ),
                    "placement_id": (
                        placement.placement_id
                    ),
                    "user_id": str(
                        order.student_id
                    ),
                    "event_type": rng.choice(
                        event_types
                    ),
                    "occurred_at": (
                        occurred_at
                    ),
                }
            )

            touch_number += 1

    if not rows:
        return pd.DataFrame(
            columns=[
                "touch_id",
                "placement_id",
                "user_id",
                "event_type",
                "occurred_at",
            ]
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "user_id",
                "occurred_at",
            ]
        )
        .reset_index(
            drop=True
        )
    )