from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd


SALES_COLUMNS = {
    "order_id",
    "student_id",
    "timestamp",
    "order_revenue",
}

PLACEMENT_COLUMNS = {
    "placement_id",
    "campaign_id",
    "creative_id",
    "channel",
    "publisher",
    "publication_at",
    "cost",
    "tracking_token",
}

TOUCH_COLUMNS = {
    "touch_id",
    "placement_id",
    "user_id",
    "event_type",
    "occurred_at",
}


def _check_columns(
    frame: pd.DataFrame,
    required: set[str],
    source: str,
) -> None:
    missing = required - set(frame.columns)

    if missing:
        columns = ", ".join(sorted(missing))
        raise ValueError(
            f"{source}: missing columns: {columns}"
        )


def load_sales_mart(
    path: Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        dtype={
            "student_id": "string",
        },
    )

    _check_columns(
        frame,
        SALES_COLUMNS,
        "sales_mart",
    )

    frame["student_id"] = (
        frame["student_id"]
        .astype(str)
    )

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        errors="raise",
    )

    frame["order_revenue"] = frame[
        "order_revenue"
    ].map(
        lambda value: Decimal(str(value))
    )

    if (
        frame["order_revenue"]
        .map(lambda value: value < 0)
        .any()
    ):
        raise ValueError(
            "sales_mart contains negative revenue"
        )

    return frame


def load_placements(
    path: Path,
) -> pd.DataFrame:
    frame = pd.read_csv(path)

    _check_columns(
        frame,
        PLACEMENT_COLUMNS,
        "mock_placements",
    )

    frame["publication_at"] = pd.to_datetime(
        frame["publication_at"],
        errors="raise",
    )

    frame["cost"] = frame["cost"].map(
        lambda value: Decimal(str(value))
    )

    if (
        frame["cost"]
        .map(lambda value: value < 0)
        .any()
    ):
        raise ValueError(
            "mock_placements contains negative cost"
        )

    if frame["placement_id"].duplicated().any():
        raise ValueError(
            "placement_id must be unique"
        )

    return frame


def load_touches(
    path: Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        dtype={
            "user_id": "string",
        },
    )

    _check_columns(
        frame,
        TOUCH_COLUMNS,
        "mock_touches",
    )

    frame["user_id"] = (
        frame["user_id"]
        .astype(str)
    )

    frame["occurred_at"] = pd.to_datetime(
        frame["occurred_at"],
        errors="raise",
    )

    if frame["touch_id"].duplicated().any():
        raise ValueError(
            "touch_id must be unique"
        )

    return frame


def save_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = frame.copy()

    for column in output.columns:
        if output[column].map(
            lambda value: isinstance(
                value,
                Decimal,
            )
        ).any():
            output[column] = output[column].map(
                lambda value: (
                    str(value)
                    if isinstance(
                        value,
                        Decimal,
                    )
                    else value
                )
            )

    output.to_csv(
        path,
        index=False,
    )