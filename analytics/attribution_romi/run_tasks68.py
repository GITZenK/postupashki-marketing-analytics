from __future__ import annotations

from src.pipeline import run_pipeline


def main() -> None:
    result = run_pipeline(
        regenerate_mock=True
    )

    print(
        f"orders: "
        f"{len(result['orders'])}"
    )

    print(
        f"placements: "
        f"{len(result['placements'])}"
    )

    print(
        f"touches: "
        f"{len(result['touches'])}"
    )

    print(
        f"attribution rows: "
        f"{len(result['attribution'])}"
    )

    print()

    print(
        result[
            "coverage"
        ].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()