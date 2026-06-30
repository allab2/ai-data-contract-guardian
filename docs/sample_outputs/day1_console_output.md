# Day 1 Console Output

Captured from:

```bash
python main.py --file data/incoming/customer_orders_day1.csv
```

## Summary

```
Running validation pipeline for: data/incoming/customer_orders_day1.csv
  -> Loaded 10 rows, 9 columns against contract customer_orders_contract.yml

========================================================================
AI DATA CONTRACT & SCHEMA DRIFT GUARDIAN - VALIDATION REPORT
========================================================================
Feed:              customer_orders_day1.csv
Overall Status:    PASS
Risk Level:        LOW
Total Issues:      0
Breaking Changes:  0

Executive Summary
-----------------
  The 'customer_orders_day1.csv' feed passed contract validation with no material
  schema drift or data quality issues.

Schema Validation
-----------------
  No schema issues detected.

Schema Drift
------------
  No schema drift detected.

Data Quality
------------
  No data quality issues detected.

Downstream Impact
-----------------
  No significant downstream impact expected. The feed aligns with the contract.

Recommended Actions
-------------------
  1. No immediate action required. Continue monitoring future deliveries.

========================================================================

Reports saved:
  JSON:     data/reports/customer_orders_day1_validation_report.json
  Markdown: data/reports/customer_orders_day1_validation_report.md
  CSV:      data/reports/customer_orders_day1_issues.csv
```
