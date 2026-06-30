# Day 2 Console Output

Captured from:

```bash
python main.py --file data/incoming/customer_orders_day2_schema_drift.csv
```

## Summary

```
Running validation pipeline for: data/incoming/customer_orders_day2_schema_drift.csv
  -> Loaded 10 rows, 11 columns against contract customer_orders_contract.yml

========================================================================
AI DATA CONTRACT & SCHEMA DRIFT GUARDIAN - VALIDATION REPORT
========================================================================
Feed:              customer_orders_day2_schema_drift.csv
Overall Status:    FAIL
Risk Level:        CRITICAL
Total Issues:      24
Breaking Changes:  3

Executive Summary
-----------------
  The 'customer_orders_day2_schema_drift.csv' feed requires attention. Found 19
  validation issues and 3 breaking schema changes. Likely column renames:
  customer_id -> cust_id, quantity -> qty, status -> order_status

Schema Validation
-----------------
  1. [HIGH] renamed_column_candidate (customer_id)
     Required column 'customer_id' is missing; 'cust_id' was added and looks like
     a rename candidate (similarity=0.95).
  2. [HIGH] renamed_column_candidate (quantity)
     Required column 'quantity' is missing; 'qty' was added and looks like a
     rename candidate (similarity=0.95).
  3. [HIGH] renamed_column_candidate (status)
     Required column 'status' is missing; 'order_status' was added and looks like
     a rename candidate (similarity=0.95).
  4. [MEDIUM] unexpected_column (discount_pct)
     Unexpected column 'discount_pct' was added to the feed.
  5. [LOW] unexpected_column (region)
     Unexpected column 'region' was added to the feed. Column contains null values.
  6. [HIGH] non_nullable_contract_violation (customer_name)
     Required column 'customer_name' contains null values (1 rows).
  7. [HIGH] non_nullable_contract_violation (product_name)
     Required column 'product_name' contains null values (1 rows).

Schema Drift
------------
  Drift detected: 3 breaking, 2 non-breaking.
  1. [HIGH] renamed_column_candidate (customer_id)
  2. [HIGH] renamed_column_candidate (quantity)
  3. [HIGH] renamed_column_candidate (status)
  4. [MEDIUM] added_column (discount_pct)
  5. [LOW] added_column (region)

Data Quality
------------
  12 issues including date format violations, range violations, negative values,
  invalid status values ('done'), and required field null violations.

Downstream Impact
-----------------
  Renamed columns can break SQL models, dbt tests, and dashboards. Breaking schema
  drift detected. Data quality failures can produce incorrect KPIs and revenue totals.

Recommended Actions
-------------------
  1. Confirm renames with vendor (customer_id, quantity, status)
  2. Review new columns (discount_pct, region)
  3. Investigate high-severity quality failures
  4. Standardize date formatting with vendor

========================================================================

Reports saved:
  JSON:     data/reports/customer_orders_day2_schema_drift_validation_report.json
  Markdown: data/reports/customer_orders_day2_schema_drift_validation_report.md
  CSV:      data/reports/customer_orders_day2_schema_drift_issues.csv
```
