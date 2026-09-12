from __future__ import annotations

import pandas as pd

from src.attribution import (
    attribute_all_models,
    build_attribution_coverage,
)
from src.config import (
    ATTRIBUTION_COVERAGE_PATH,
    ATTRIBUTION_RESULTS_PATH,
    CONTRIBUTION_MARGIN_SCENARIOS,
    DEFAULT_ATTRIBUTION_WINDOW_DAYS,
    DEFAULT_CONTRIBUTION_MARGIN_RATE,
    MOCK_PLACEMENTS_PATH,
    MOCK_TOUCHES_PATH,
    ROMI_BY_CAMPAIGN_PATH,
    ROMI_BY_PLACEMENT_PATH,
    ROMI_BY_PUBLISHER_PATH,
    ROMI_SENSITIVITY_PATH,
    SALES_MART_PATH,
    SENSITIVITY_WINDOWS,
)
from src.io_utils import (
    load_placements,
    load_sales_mart,
    load_touches,
    save_csv,
)
from src.mock_data import (
    build_mock_placements,
    build_mock_touches,
)
from src.romi import (
    calculate_romi_by_campaign,
    calculate_romi_by_placement,
    calculate_romi_by_publisher,
)


def generate_mock_inputs(
    orders: pd.DataFrame,
) -> None:
    placements = (
        build_mock_placements()
    )

    touches = build_mock_touches(
        orders=orders,
        placements=placements,
    )

    save_csv(
        placements,
        MOCK_PLACEMENTS_PATH,
    )

    save_csv(
        touches,
        MOCK_TOUCHES_PATH,
    )


def calculate_sensitivity(
    orders: pd.DataFrame,
    touches: pd.DataFrame,
    placements: pd.DataFrame,
) -> pd.DataFrame:
    frames: list[
        pd.DataFrame
    ] = []

    for window_days in (
        SENSITIVITY_WINDOWS
    ):
        attribution = (
            attribute_all_models(
                orders=orders,
                touches=touches,
                placements=placements,
                window_days=(
                    window_days
                ),
            )
        )

        for margin_rate in (
            CONTRIBUTION_MARGIN_SCENARIOS
        ):
            placement_romi = (
                calculate_romi_by_placement(
                    attribution=(
                        attribution
                    ),
                    placements=(
                        placements
                    ),
                    contribution_margin_rate=(
                        margin_rate
                    ),
                )
            )

            campaign_romi = (
                calculate_romi_by_campaign(
                    placement_romi
                )
            )

            campaign_romi[
                "attribution_window_days"
            ] = window_days

            campaign_romi[
                "cm_rate"
            ] = margin_rate

            frames.append(
                campaign_romi
            )

    return pd.concat(
        frames,
        ignore_index=True,
    )


def run_pipeline(
    regenerate_mock: bool = True,
) -> dict[str, pd.DataFrame]:
    orders = load_sales_mart(
        SALES_MART_PATH
    )

    if regenerate_mock:
        generate_mock_inputs(
            orders
        )

    placements = load_placements(
        MOCK_PLACEMENTS_PATH
    )

    touches = load_touches(
        MOCK_TOUCHES_PATH
    )

    attribution = (
        attribute_all_models(
            orders=orders,
            touches=touches,
            placements=placements,
            window_days=(
                DEFAULT_ATTRIBUTION_WINDOW_DAYS
            ),
        )
    )

    coverage = (
        build_attribution_coverage(
            orders=orders,
            attribution=attribution,
        )
    )

    placement_romi = (
        calculate_romi_by_placement(
            attribution=attribution,
            placements=placements,
            contribution_margin_rate=(
                DEFAULT_CONTRIBUTION_MARGIN_RATE
            ),
        )
    )

    campaign_romi = (
        calculate_romi_by_campaign(
            placement_romi
        )
    )

    publisher_romi = (
        calculate_romi_by_publisher(
            placement_romi
        )
    )

    sensitivity = (
        calculate_sensitivity(
            orders=orders,
            touches=touches,
            placements=placements,
        )
    )

    save_csv(
        attribution,
        ATTRIBUTION_RESULTS_PATH,
    )

    save_csv(
        coverage,
        ATTRIBUTION_COVERAGE_PATH,
    )

    save_csv(
        placement_romi,
        ROMI_BY_PLACEMENT_PATH,
    )

    save_csv(
        campaign_romi,
        ROMI_BY_CAMPAIGN_PATH,
    )

    save_csv(
        publisher_romi,
        ROMI_BY_PUBLISHER_PATH,
    )

    save_csv(
        sensitivity,
        ROMI_SENSITIVITY_PATH,
    )

    return {
        "orders": orders,
        "placements": placements,
        "touches": touches,
        "attribution": attribution,
        "coverage": coverage,
        "romi_by_placement": (
            placement_romi
        ),
        "romi_by_campaign": (
            campaign_romi
        ),
        "romi_by_publisher": (
            publisher_romi
        ),
        "romi_sensitivity": (
            sensitivity
        ),
    }