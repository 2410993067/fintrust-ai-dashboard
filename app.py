import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import inspect, text
from models import db, Transaction
import pandas as pd
from utils import build_dashboard_payload, clean_transactions

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///transactions.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "portfolio-dev-secret")

db.init_app(app)

with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    if "transaction" in inspector.get_table_names():
        existing_columns = [col["name"] for col in inspector.get_columns("transaction")]
        if "is_subscription" not in existing_columns:
            db.session.execute(
                text('ALTER TABLE "transaction" ADD COLUMN is_subscription BOOLEAN NOT NULL DEFAULT 0')
            )
            db.session.commit()
        if "transaction_type" not in existing_columns:
            db.session.execute(
                text('ALTER TABLE "transaction" ADD COLUMN transaction_type VARCHAR(32) NOT NULL DEFAULT \'\'')
            )
            db.session.commit()
        if "mcc" not in existing_columns:
            db.session.execute(
                text('ALTER TABLE "transaction" ADD COLUMN mcc VARCHAR(64) NOT NULL DEFAULT \'\'')
            )
            db.session.commit()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or file.filename == "":
            flash("Please choose a CSV file to upload.", "warning")
            return redirect(url_for("index"))

        try:
            df = clean_transactions(file)
            Transaction.query.delete()
            records = df.to_dict(orient="records")
            for record in records:
                record["date"] = record["date"].strftime("%Y-%m-%d")
            db.session.bulk_insert_mappings(Transaction, records)
            db.session.commit()
            flash(f"Imported {len(df)} transactions.", "success")
        except Exception as error:
            db.session.rollback()
            flash(f"Failed to process CSV: {error}", "danger")
        return redirect(url_for("index"))

    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template("index.html", transactions=transactions)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/dashboard")
def api_dashboard():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    if not transactions:
        return jsonify({
            "total_transactions": 0,
            "total_spending": 0.0,
            "monthly_subscription_cost": 0.0,
            "health_score": 100,
            "health_label": "Excellent",
            "subscriptions": [],
            "chart_labels": [],
            "chart_values": [],
        })

    df = pd.DataFrame([
        {
            "date": txn.date,
            "amount": txn.amount,
            "merchant": txn.merchant,
            "mcc": txn.mcc,
            "transaction_type": txn.transaction_type,
        }
        for txn in transactions
    ])
    analytics = build_dashboard_payload(df)
    return jsonify(analytics)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
