# Subscription Insights

A student-built Flask fintech dashboard that cleans bank transaction CSVs, detects recurring merchant patterns, and highlights likely subscription spending in a simple SaaS-style interface.

## Features

- Upload transaction CSV files through a drag-and-drop interface
- Clean and normalize transaction columns from varied bank export formats
- Detect recurring merchants using interval and amount consistency
- View total transactions, net spending, monthly subscription cost, and a financial health score
- Explore recurring merchant summaries in both chart and table form

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Pandas
- Bootstrap 5
- Chart.js

## Project Structure

```text
fintech/
|-- app.py
|-- models.py
|-- utils.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- dataset/
|   `-- sample_transactions.csv
|-- static/
|   |-- css/
|   |   |-- dashboard.css
|   |   `-- index.css
|   `-- js/
|       |-- dashboard.js
|       `-- index.js
|-- templates/
|   |-- dashboard.html
|   `-- index.html
`-- tests/
    `-- test_app.py
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Sample Data

Use `dataset/sample_transactions.csv` to test the upload flow quickly.

The original large export file used during development is intentionally excluded from GitHub through `.gitignore` because it is too large for a portfolio repository and not needed to demonstrate the app.

## Running Tests

```bash
python -m unittest discover -s tests
```

## Portfolio Notes

- The dashboard metrics are calculated from the uploaded dataframe rather than hardcoded demo values.
- Uploaded data is stored locally in a SQLite database inside Flask's `instance/` folder.
- The app is designed as a clean student portfolio project, not a production banking platform.

## Recommended GitHub Repo Description

`Flask fintech dashboard for subscription detection and recurring spend analysis from CSV transaction data.`
