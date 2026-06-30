# Day 2 Markdown Report Preview

Source file: `data/reports/customer_orders_day2_schema_drift_validation_report.md`

---

# Validation Report: customer_orders_day2_schema_drift.csv

**Run timestamp:** 2026-06-30T19:38:45.597523+00:00

## Executive Summary

The 'customer_orders_day2_schema_drift.csv' feed requires attention. Found 19 validation issues and 3 breaking schema changes. Likely column renames: customer_id -> cust_id, quantity -> qty, status -> order_status

## Overall Status

- **Status:** FAIL
- **Risk level:** CRITICAL
- **Breaking changes:** 3
- **Total issues:** 24

## Schema Validation

- **[HIGH]** `renamed_column_candidate` (customer_id): Required column 'customer_id' is missing; 'cust_id' was added and looks like a rename candidate (similarity=0.95).
- **[HIGH]** `renamed_column_candidate` (quantity): Required column 'quantity' is missing; 'qty' was added and looks like a rename candidate (similarity=0.95).
- **[HIGH]** `renamed_column_candidate` (status): Required column 'status' is missing; 'order_status' was added and looks like a rename candidate (similarity=0.95).
- **[MEDIUM]** `unexpected_column` (discount_pct): Unexpected column 'discount_pct' was added to the feed.
- **[LOW]** `unexpected_column` (region): Unexpected column 'region' was added to the feed. Column contains null values.
- **[HIGH]** `non_nullable_contract_violation` (customer_name): Required column 'customer_name' contains null values (1 rows).
- **[HIGH]** `non_nullable_contract_violation` (product_name): Required column 'product_name' contains null values (1 rows).

## Schema Drift

Drift detected: 3 breaking, 2 non-breaking.

- **[HIGH]** `renamed_column_candidate` (customer_id, breaking): Possible rename detected: 'customer_id' -> 'cust_id' (similarity=0.95).
- **[HIGH]** `renamed_column_candidate` (quantity, breaking): Possible rename detected: 'quantity' -> 'qty' (similarity=0.95).
- **[HIGH]** `renamed_column_candidate` (status, breaking): Possible rename detected: 'status' -> 'order_status' (similarity=0.95).
- **[MEDIUM]** `added_column` (discount_pct, non-breaking): New column 'discount_pct' is not defined in the contract.
- **[LOW]** `added_column` (region, non-breaking): New column 'region' is not defined in the contract.

## Data Quality Issues

- **[CRITICAL]** `allowed_values_violation` (status): Column 'status' has 3 values outside allowed set.
- **[CRITICAL]** `range_violation` (quantity): Column 'quantity' has 3 values outside allowed range [1, 500].
- **[HIGH]** `date_format_violation` (order_date): Column 'order_date' has 9 values that do not match expected date format '%Y-%m-%d'.
- Additional null, range, and negative-value violations — see full report in `data/reports/`.

## Recommended Actions

1. Confirm with the vendor whether 'customer_id' was renamed to 'cust_id' and update the contract or ingestion mapping.
2. Confirm with the vendor whether 'quantity' was renamed to 'qty' and update the contract or ingestion mapping.
3. Confirm with the vendor whether 'status' was renamed to 'order_status' and update the contract or ingestion mapping.
4. Review newly added columns and decide whether to add them to the contract: discount_pct, region.
5. Investigate high-severity data quality failures and reject or quarantine rows before loading into production tables.
6. Standardize date formatting with the vendor or add a parsing rule in ingestion.

## Downstream Impact

Renamed columns (customer_id->cust_id, quantity->qty, status->order_status) can break SQL models, dbt tests, and dashboards that reference the original names. Breaking schema drift detected. Downstream consumers expecting the contract schema may fail at load time. Data quality failures can produce incorrect KPIs, revenue totals, and customer-level metrics.
