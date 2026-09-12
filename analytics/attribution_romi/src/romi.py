from __future__ import annotations

from decimal import Decimal

import pandas as pd

from src.attribution import (
    SUPPORTED_MODELS,
)
from src.config import (
    DEFAULT_CONTRIBUTION_MARGIN_RATE,
)


ZERO = Decimal("0")
ONE = Decimal("1")


def _calculate_romi(
    attributed_value: Decimal,
    cost: Decimal,
) -> Decimal | None:
    if cost == 0:
        return None

    return (
        attributed_value - cost
    ) / cost


def _build_placement_base(
    placements: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[
        dict[str, object]
    ] = []

    for model in SUPPORTED_MODELS:
        for placement in placements.itertuples(
            index=False
        ):
            rows.append(
                {
                    "model": model,
                    "placement_id": (
                        placement.placement_id
                    ),
                    "campaign_id": (
                        placement.campaign_id
                    ),
                    "channel": (
                        placement.channel
                    ),
                    "publisher": (
                        placement.publisher
                    ),
                    "cost": Decimal(
                        str(
                            placement.cost
                        )
                    ),
                }
            )

    return pd.DataFrame(rows)


def calculate_romi_by_placement(
    attribution: pd.DataFrame,
    placements: pd.DataFrame,
    contribution_margin_rate: Decimal = DEFAULT_CONTRIBUTION_MARGIN_RATE,
) -> pd.DataFrame:
    if not (
        ZERO
        <= contribution_margin_rate
        <= ONE
    ):
        raise ValueError(
            "Contribution margin rate "
            "must be between 0 and 1"
        )

    if attribution.empty:
        revenue = pd.DataFrame(
            columns=[
                "model",
                "placement_id",
                "attributed_revenue",
            ]
        )
    else:
        revenue = (
            attribution
            .groupby(
                [
                    "model",
                    "placement_id",
                ],
                as_index=False,
            )
            .agg(
                attributed_revenue=(
                    "attributed_revenue",
                    lambda values: sum(
                        values,
                        ZERO,
                    ),
                )
            )
        )

    base = _build_placement_base(
        placements
    )

    result = base.merge(
        revenue,
        on=[
            "model",
            "placement_id",
        ],
        how="left",
    )

    result[
        "attributed_revenue"
    ] = result[
        "attributed_revenue"
    ].map(
        lambda value: (
            ZERO
            if pd.isna(value)
            else Decimal(
                str(value)
            )
        )
    )

    result[
        "contribution_margin_rate"
    ] = contribution_margin_rate

    result[
        "attributed_contribution"
    ] = result[
        "attributed_revenue"
    ].map(
        lambda value: (
            value
            * contribution_margin_rate
        )
    )

    result["romi_attr"] = result.apply(
        lambda row: _calculate_romi(
            attributed_value=row[
                "attributed_revenue"
            ],
            cost=row["cost"],
        ),
        axis=1,
    )

    result[
        "romi_contribution"
    ] = result.apply(
        lambda row: _calculate_romi(
            attributed_value=row[
                "attributed_contribution"
            ],
            cost=row["cost"],
        ),
        axis=1,
    )

    return result


def _aggregate_romi(
    placement_romi: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    result = (
        placement_romi
        .groupby(
            [
                "model",
                *group_columns,
            ],
            as_index=False,
        )
        .agg(
            attributed_revenue=(
                "attributed_revenue",
                lambda values: sum(
                    values,
                    ZERO,
                ),
            ),
            attributed_contribution=(
                "attributed_contribution",
                lambda values: sum(
                    values,
                    ZERO,
                ),
            ),
            cost=(
                "cost",
                lambda values: sum(
                    values,
                    ZERO,
                ),
            ),
            contribution_margin_rate=(
                "contribution_margin_rate",
                "first",
            ),
        )
    )

    result["romi_attr"] = result.apply(
        lambda row: _calculate_romi(
            attributed_value=row[
                "attributed_revenue"
            ],
            cost=row["cost"],
        ),
        axis=1,
    )

    result[
        "romi_contribution"
    ] = result.apply(
        lambda row: _calculate_romi(
            attributed_value=row[
                "attributed_contribution"
            ],
            cost=row["cost"],
        ),
        axis=1,
    )

    return result


def calculate_romi_by_campaign(
    placement_romi: pd.DataFrame,
) -> pd.DataFrame:
    return _aggregate_romi(
        placement_romi=placement_romi,
        group_columns=[
            "campaign_id",
        ],
    )


def calculate_romi_by_publisher(
    placement_romi: pd.DataFrame,
) -> pd.DataFrame:
    return _aggregate_romi(
        placement_romi=placement_romi,
        group_columns=[
            "channel",
            "publisher",
        ],
    )