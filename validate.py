"""Step 3 - validate: separate good rows from bad rows and write an audit trail."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from etl.config import LOG_DIR

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["order_id", "order_date", "product_id", "store_id"]

RULE_CHECKS = [
    ("missing required field", lambda df: df[REQUIRED_COLUMNS].isna().any(axis=1)),
    ("invalid order date", lambda df: df["order_date"].isna()),
    ("quantity must be a positive number", lambda df: ~(df["quantity"] > 0)),
    ("unit price must be zero or more", lambda df: ~(df["unit_price"] >= 0)),
    ("discount must be between 0 and 1", lambda df: ~df["discount"].between(0, 1)),
]


def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (valid_rows, rejected_rows, report).

    Every failing row gets a `rejection_reason` so the pipeline can be audited
    instead of quietly losing data.
    """
    # One column per rule, True where the row breaks that rule.
    failures = pd.DataFrame(
        {label: check(df).fillna(True) for label, check in RULE_CHECKS}, index=df.index
    )
    reasons = failures.apply(
        lambda row: "; ".join(rule for rule in failures.columns if row[rule]), axis=1
    )

    failed = reasons != ""
    rejected = df.loc[failed].copy()
    rejected["rejection_reason"] = reasons.loc[failed]
    valid = df.loc[~failed].copy()

    duplicates = valid.duplicated(subset=["order_id", "product_id"], keep="first")
    duplicate_rows = int(duplicates.sum())
    valid = valid.loc[~duplicates].copy()

    report = {
        "raw_rows": int(len(df)),
        "invalid_rows": int(len(rejected)),
        "duplicate_rows_removed": duplicate_rows,
        "valid_rows": int(len(valid)),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not rejected.empty:
        rejected.to_csv(LOG_DIR / "rejected_records.csv", index=False)

    report_lines = [
        "Retail sales pipeline - data quality report",
        f"Generated at      : {report['generated_at']}",
        f"Rows extracted    : {report['raw_rows']:,}",
        f"Rows rejected     : {report['invalid_rows']:,}",
        f"Duplicates removed: {report['duplicate_rows_removed']:,}",
        f"Rows loaded       : {report['valid_rows']:,}",
        "",
        "Rejections by reason:",
    ]
    if rejected.empty:
        report_lines.append("  none")
    else:
        for reason, count in rejected["rejection_reason"].value_counts().items():
            report_lines.append(f"  {reason}: {count:,}")
    (LOG_DIR / "validation_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    logger.info(
        "Validation: %s valid rows, %s rejected, %s duplicates removed",
        f"{report['valid_rows']:,}",
        f"{report['invalid_rows']:,}",
        f"{report['duplicate_rows_removed']:,}",
    )
    return valid, rejected, report
