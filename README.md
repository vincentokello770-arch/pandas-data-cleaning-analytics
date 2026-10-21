# Kenyan Retail Data Quality & Analytics Pipeline

**Author:** Vincent Kenyatta  
**Technologies:** Python, pandas, NumPy, Matplotlib, SQLite-ready CSV data workflows, pytest, Git

## Project Overview

This project demonstrates how to transform a messy retail sales dataset into validated, analysis-ready data using a reproducible Python pipeline.

The dataset is entirely synthetic and represents a fictional Kenyan retailer. It contains realistic data-quality problems such as missing customer identifiers, inconsistent text labels, mixed date formats, duplicate records, and invalid quantities or prices.

## Business Problem

Retail reporting is only as reliable as the underlying data. Inconsistent and invalid sales records can distort revenue calculations, product comparisons, and business decisions.

This project addresses that problem by generating sample data, profiling its quality, cleaning and validating records, documenting rejected rows, and producing analytical reports and visualizations.

## Project Objectives

- Generate reproducible synthetic Kenyan retail sales data.
- Profile missing values and data-quality issues.
- Normalize inconsistent fields and date formats.
- Remove exact duplicate records.
- Separate rejected records and record rejection reasons.
- Calculate net sales and produce sales analytics.
- Validate the output with automated checks and tests.
- Create a reproducible, documented portfolio project.

## Technology Stack

- **Python 3.10** — pipeline execution.
- **pandas** — data cleaning and analysis.
- **NumPy** — numerical operations and data handling.
- **Matplotlib** — charts and visualizations.
- **pytest** — automated testing.
- **PowerShell** — Windows command-line workflow.

## Project Structure

```text
pandas-data-cleaning-analytics/
├── data/
│   ├── raw/                 # Generated source dataset
│   └── processed/           # Clean and rejected records
├── reports/
│   ├── charts/              # Generated visualizations
│   ├── data_quality_report.csv
│   ├── monthly_sales.csv
│   ├── sales_by_category.csv
│   ├── sales_by_county.csv
│   ├── sales_by_payment_method.csv
│   ├── sales_kpis.csv
│   └── top_10_products.csv
├── src/
│   ├── generate_data.py
│   ├── profile_data.py
│   ├── clean_data.py
│   └── analyze_data.py
├── tests/
├── validate_clean_data.py
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

## Environment Setup

Run these commands from the project root in Windows PowerShell. They explicitly use Python 3.10 rather than whichever Python version the launcher selects by default.

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

## Run the Pipeline

Run each stage from the project root:

```powershell
& ".\.venv\Scripts\python.exe" .\src\generate_data.py
& ".\.venv\Scripts\python.exe" .\src\profile_data.py
& ".\.venv\Scripts\python.exe" .\src\clean_data.py
& ".\.venv\Scripts\python.exe" .\validate_clean_data.py
& ".\.venv\Scripts\python.exe" .\src\analyze_data.py
& ".\.venv\Scripts\python.exe" -m pytest -q
```

Run the stages in order because later stages depend on files produced earlier. The generator uses a fixed random seed for reproducibility.

## Latest Verified Results

The current generated dataset produced the following results:

| Metric | Result |
|---|---:|
| Raw records | 150,060 |
| Exact duplicate records removed | 60 |
| Records after deduplication | 150,000 |
| Rejected records | 2,775 |
| Clean records retained | 147,225 |
| Clean-record retention rate | 98.15% |
| Unique orders in clean data | 74,970 |
| Total units sold | 525,600 |
| Total net sales | KES 3,231,342,563.01 |
| Average order value | KES 43,101.81 |
| Data-validation checks passed | 24 of 24 |
| Automated tests passed | 2 |

These results are from fictional data and are intended for demonstrating technical methods, not describing actual Kenyan retail performance.

## Generated Outputs

The pipeline creates:

- A cleaned sales dataset.
- A separate file of rejected records and rejection reasons.
- A data-quality report.
- Key performance indicator summaries.
- Monthly sales and category, county, payment-method, and product reports.
- Charts for sales trends, category performance, payment methods, and leading counties.
- Validation and automated test results.

Generated datasets are excluded from Git by default to avoid unnecessarily large repositories. They can be recreated by running the pipeline.

## Data Quality and Limitations

- The dataset is synthetic and contains no real customer or student records.
- Missing customer IDs are retained where the cleaning rules allow them; missing identifiers should not automatically be treated as invalid sales.
- Rejected records are separated for review rather than silently discarded.
- Revenue, order counts, and other metrics depend on the documented cleaning and aggregation rules.
- The current validation checks cover defined data-quality conditions but do not guarantee that every possible business issue has been detected.

## Future Improvements

- Add more edge-case and regression tests.
- Document the data model and analytical assumptions in greater depth.
- Load the cleaned data into SQLite and PostgreSQL.
- Build an interactive Power BI dashboard.
- Add a GitHub Actions workflow to run tests automatically.
- Compare alternative cleaning rules and measure their impact on reported KPIs.

## Skills Demonstrated

Data profiling, missing-value analysis, date parsing, duplicate detection, data validation, transformation pipelines, rejection auditing, KPI calculation, exploratory data analysis, visualization, automated testing, reproducibility, and technical documentation.

## Author

**Vincent Kenyatta**  
ICT Professional | Data Analytics | Python | Cloud Engineering

This project is part of a practical portfolio focused on data analytics and engineering skills.
