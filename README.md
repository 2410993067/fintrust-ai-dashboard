# Subscription Insights – Fintech Analytics Dashboard

A clean, student-built fintech dashboard that analyzes transaction data to uncover spending patterns, detect recurring subscriptions, and provide simple financial insights through an intuitive SaaS-style interface.

---

## Overview

Managing personal finances from raw bank statements can be confusing and time-consuming.  
This project simplifies that process by transforming transaction CSV data into meaningful insights such as recurring expenses, total spending, and financial health indicators.

---

## Features

- Upload transaction CSV files via a drag-and-drop interface  
- Clean and normalize data from different bank formats  
- Detect recurring merchants using pattern analysis  
- Calculate total spending and subscription costs  
- Visualize insights using charts and tables  
- Generate a financial health score  

---

## How It Works

1. User uploads transaction CSV  
2. Data is cleaned and standardized using Pandas  
3. Recurring merchants are detected based on frequency and consistency  
4. Insights are calculated and displayed on a dashboard  

---

## Tech Stack

- Python, Flask  
- Pandas (Data Processing)  
- Flask-SQLAlchemy  
- Bootstrap 5  
- Chart.js  

---

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
