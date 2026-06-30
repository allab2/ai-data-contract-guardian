.PHONY: install test run-day1 run-day2 dashboard clean-reports screenshots

PYTHON ?= python3
PIP ?= pip

install:
	$(PIP) install -r requirements.txt

test:
	pytest tests/ -v

run-day1:
	$(PYTHON) main.py --file data/incoming/customer_orders_day1.csv

run-day2:
	$(PYTHON) main.py --file data/incoming/customer_orders_day2_schema_drift.csv

dashboard:
	streamlit run src/app/streamlit_app.py

clean-reports:
	rm -f data/reports/*

screenshots:
	$(PYTHON) scripts/generate_screenshot_assets.py
