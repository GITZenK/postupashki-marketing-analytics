from __future__ import annotations

from decimal import Decimal
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = MODULE_ROOT.parent.parent

DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = MODULE_ROOT / "outputs"

SALES_MART_PATH = DATA_DIR / "sales_mart.csv"

MOCK_PLACEMENTS_PATH = OUTPUT_DIR / "mock_placements.csv"
MOCK_TOUCHES_PATH = OUTPUT_DIR / "mock_touches.csv"

ATTRIBUTION_RESULTS_PATH = OUTPUT_DIR / "attribution_results.csv"
ATTRIBUTION_COVERAGE_PATH = OUTPUT_DIR / "attribution_coverage.csv"

ROMI_BY_PLACEMENT_PATH = OUTPUT_DIR / "romi_by_placement.csv"
ROMI_BY_CAMPAIGN_PATH = OUTPUT_DIR / "romi_by_campaign.csv"
ROMI_BY_PUBLISHER_PATH = OUTPUT_DIR / "romi_by_publisher.csv"
ROMI_SENSITIVITY_PATH = OUTPUT_DIR / "romi_sensitivity.csv"


DEFAULT_ATTRIBUTION_WINDOW_DAYS = 30

SENSITIVITY_WINDOWS = (
    7,
    14,
    30,
    60,
    90,
)


TIME_DECAY_HALF_LIFE_DAYS = 7

POSITION_BASED_FIRST_WEIGHT = Decimal("0.4")
POSITION_BASED_LAST_WEIGHT = Decimal("0.4")


DEFAULT_CONTRIBUTION_MARGIN_RATE = Decimal("0.6")

CONTRIBUTION_MARGIN_SCENARIOS = (
    Decimal("0.4"),
    Decimal("0.5"),
    Decimal("0.6"),
    Decimal("0.7"),
)


MOCK_ORGANIC_SHARE = 0.25

MOCK_MIN_TOUCHES = 1
MOCK_MAX_TOUCHES = 3

MOCK_RANDOM_SEED = 42