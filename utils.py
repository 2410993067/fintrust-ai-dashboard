import pandas as pd
import re
from thefuzz import process


DATE_COLUMN_CANDIDATES = ["date", "txn_date", "transaction_date"]
AMOUNT_COLUMN_CANDIDATES = ["amount", "amt", "value"]
MERCHANT_COLUMN_CANDIDATES = ["merchant_id", "merchant", "description", "details"]
MAX_UPLOAD_ROWS = 5000


def normalize_amount(series):
    def parse_amount(value):
        text = str(value)
        text = re.sub(r"[,$]", "", text)
        text = re.sub(r"[^0-9.\-]", "", text)
        try:
            return float(text)
        except ValueError:
            return 0.0

    return series.apply(parse_amount)


def normalize_description(series):
    return series.fillna("").astype(str).str.strip()


def group_similar_merchants(merchants, threshold=85):
    merchant_map = {}
    group_names = []

    for merchant in merchants:
        if not merchant:
            merchant_map[merchant] = "Unknown Merchant"
            continue

        if not group_names:
            group_names.append(merchant)
            merchant_map[merchant] = merchant
            continue

        best_match, score = process.extractOne(merchant, group_names)
        if best_match and score >= threshold:
            merchant_map[merchant] = best_match
        else:
            group_names.append(merchant)
            merchant_map[merchant] = merchant

    return merchant_map


def resolve_column_name(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def detect_subscriptions(df, interval_min=25, interval_max=35, interval_std_max=5, amount_std_ratio=0.1, max_gap_days=90):
    """
    Identify subscription merchants and return summary metrics.
    """
    summary = []
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for merchant_group, group in df.groupby("merchant_group", sort=False):
        group = group.dropna(subset=["date", "amount"]).sort_values("date")
        if len(group) < 3:
            continue

        diffs = group["date"].diff().dt.days.dropna()
        if diffs.empty:
            continue

        if diffs.max() > max_gap_days:
            continue

        mean_interval = diffs.mean()
        interval_std = diffs.std(ddof=0)
        amounts = group["amount"].abs()
        mean_amount = amounts.mean()
        amount_std = amounts.std(ddof=0)

        if mean_amount == 0:
            amount_ok = amount_std <= 1.0
        else:
            amount_ok = amount_std <= mean_amount * amount_std_ratio

        interval_ok = interval_min <= mean_interval <= interval_max and interval_std < interval_std_max

        if mean_interval > 0:
            interval_score = 1 - (interval_std / mean_interval)
        else:
            interval_score = 0.0

        if mean_amount > 0:
            amount_score = 1 - (amount_std / mean_amount)
        else:
            amount_score = 0.0

        interval_score = max(0.0, min(1.0, float(interval_score)))
        amount_score = max(0.0, min(1.0, float(amount_score)))
        confidence = (interval_score + amount_score) / 2

        if interval_ok and amount_ok:
            if confidence > 0.8:
                subscription_type = "high_confidence"
            elif confidence > 0.6:
                subscription_type = "medium"
            else:
                subscription_type = "low"

            summary.append({
                "merchant": merchant_group,
                "category": group["mcc"].mode().iloc[0] if "mcc" in group.columns and not group["mcc"].mode().empty else "",
                "avg_amount": mean_amount,
                "avg_interval": mean_interval,
                "confidence_score": confidence,
                "monthly_cost": mean_amount,
                "subscription_type": subscription_type,
            })

    result = pd.DataFrame(summary)
    if not result.empty:
        result = result.sort_values("confidence_score", ascending=False).reset_index(drop=True)
        result.attrs["total_monthly_subscription_cost"] = result["monthly_cost"].sum()
    else:
        result.attrs["total_monthly_subscription_cost"] = 0.0

    return result


def build_dashboard_payload(df):
    df = df.copy()
    if df.empty:
        return {
            "total_transactions": 0,
            "total_spending": 0.0,
            "monthly_subscription_cost": 0.0,
            "health_score": 100,
            "health_label": "Excellent",
            "subscriptions": [],
            "chart_labels": [],
            "chart_values": [],
        }

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "merchant" not in df.columns:
        df["merchant"] = ""
    if "mcc" not in df.columns:
        df["mcc"] = ""

    df = df.dropna(subset=["date", "amount"])
    df = df[df["merchant"].fillna("").astype(str).str.strip() != ""].copy()
    df["merchant"] = normalize_description(df["merchant"])
    df["mcc"] = normalize_description(df["mcc"])
    df["month"] = df["date"].dt.to_period("M")

    if df.empty:
        return {
            "total_transactions": 0,
            "total_spending": 0.0,
            "monthly_subscription_cost": 0.0,
            "health_score": 100,
            "health_label": "Excellent",
            "subscriptions": [],
            "chart_labels": [],
            "chart_values": [],
        }

    subscription_records = []
    grouped = df.sort_values("date").groupby("merchant", sort=False)
    for merchant, group in grouped:
        unique_dates = group["date"].dt.normalize().nunique()
        unique_months = group["month"].nunique()
        if unique_dates < 3:
            continue

        month_counts = group.groupby("month").size()
        recurring_frequency = int((month_counts >= 1).sum())
        interval_days = group["date"].sort_values().diff().dt.days.dropna()
        mean_interval = float(interval_days.mean()) if not interval_days.empty else 0.0
        monthly_pattern = not interval_days.empty and interval_days.between(25, 35).mean() >= 0.5
        recurring_match = unique_dates >= 3 or recurring_frequency >= 3 or monthly_pattern
        if not recurring_match:
            continue

        amounts = group["amount"].abs()
        mean_amount = float(amounts.mean()) if not amounts.empty else 0.0
        interval_std = float(interval_days.std(ddof=0)) if not interval_days.empty else 0.0
        amount_std = float(amounts.std(ddof=0)) if len(amounts) > 1 else 0.0

        interval_score = 1 - (interval_std / mean_interval) if mean_interval > 0 else 0.0
        amount_score = 1 - (amount_std / mean_amount) if mean_amount > 0 else 0.0
        interval_score = max(0.0, min(1.0, float(interval_score)))
        amount_score = max(0.0, min(1.0, float(amount_score)))
        confidence_score = (interval_score + amount_score) / 2

        if confidence_score >= 0.8:
            subscription_type = "high_confidence"
        elif confidence_score >= 0.6:
            subscription_type = "medium"
        else:
            subscription_type = "low"

        category = group["mcc"].mode().iloc[0] if not group["mcc"].mode().empty else ""
        subscription_records.append({
            "merchant": merchant,
            "category": category,
            "avg_amount": mean_amount,
            "avg_interval": mean_interval,
            "confidence_score": confidence_score,
            "monthly_cost": mean_amount,
            "subscription_type": subscription_type,
        })

    subscription_records = sorted(
        subscription_records,
        key=lambda item: item["confidence_score"],
        reverse=True,
    )

    total_transactions = int(len(df))
    total_spending = float(df["amount"].sum())
    monthly_subscription_cost = float(sum(item["monthly_cost"] for item in subscription_records))

    health_score = 100
    spending_base = abs(total_spending)
    subscription_ratio = (monthly_subscription_cost / spending_base) if spending_base > 0 else 0.0
    if subscription_ratio > 0.2:
        health_score -= 20
    elif subscription_ratio > 0.1:
        health_score -= 10
    health_score = max(0, min(100, health_score))

    if health_score >= 80:
        health_label = "Excellent"
    elif health_score >= 60:
        health_label = "Good"
    else:
        health_label = "Needs Attention"

    return {
        "total_transactions": total_transactions,
        "total_spending": total_spending,
        "monthly_subscription_cost": monthly_subscription_cost,
        "health_score": health_score,
        "health_label": health_label,
        "subscriptions": subscription_records,
        "chart_labels": [item["merchant"] for item in subscription_records],
        "chart_values": [round(item["monthly_cost"], 2) for item in subscription_records],
    }


def clean_transactions(file_path):
    """
    Load and clean transaction data from a CSV file or file-like object.
    
    Args:
        file_path (str | file-like): Path to the CSV file or uploaded file stream
        
    Returns:
        pd.DataFrame: Cleaned dataframe ready for analysis
    """
    # Keep portfolio uploads responsive when large bank exports are used.
    df = pd.read_csv(file_path).head(MAX_UPLOAD_ROWS)
    
    df.columns = df.columns.str.lower()
    date_col = resolve_column_name(df.columns, DATE_COLUMN_CANDIDATES)
    amount_col = resolve_column_name(df.columns, AMOUNT_COLUMN_CANDIDATES)
    merchant_col = resolve_column_name(df.columns, MERCHANT_COLUMN_CANDIDATES)

    missing_fields = []
    if date_col is None:
        missing_fields.append(f"date column ({', '.join(DATE_COLUMN_CANDIDATES)})")
    if amount_col is None:
        missing_fields.append(f"amount column ({', '.join(AMOUNT_COLUMN_CANDIDATES)})")
    if merchant_col is None:
        missing_fields.append(f"merchant column ({', '.join(MERCHANT_COLUMN_CANDIDATES)})")

    if missing_fields:
        raise ValueError(
            "CSV is missing required columns: "
            + "; ".join(missing_fields)
            + "."
        )

    rename_map = {}
    if date_col != "date":
        rename_map[date_col] = "date"
    if amount_col != "amount":
        rename_map[amount_col] = "amount"
    if merchant_col != "merchant":
        rename_map[merchant_col] = "merchant"
    if rename_map:
        df = df.rename(columns=rename_map)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = normalize_amount(df["amount"])
    df["merchant"] = normalize_description(df["merchant"])
    if "mcc" in df.columns:
        df["mcc"] = normalize_description(df["mcc"])
    else:
        df["mcc"] = ""

    df = df.dropna(subset=["date", "amount"])
    df = df[df["merchant"] != ""].copy()
    df = df.sort_values("date").reset_index(drop=True)
    
    df["absolute_amount"] = df["amount"].abs()
    df["transaction_type"] = df["amount"].apply(lambda x: "debit" if x < 0 else "credit")
    df["original_description"] = df["merchant"]
    df["cleaned_description"] = df["merchant"]

    merchant_map = group_similar_merchants(df["merchant"].unique())
    df["merchant_group"] = df["merchant"].map(merchant_map)

    subscription_df = detect_subscriptions(df)
    subscription_merchants = subscription_df["merchant"].tolist() if not subscription_df.empty else []
    df["is_subscription"] = df["merchant_group"].isin(subscription_merchants)
    df.attrs["subscription_records"] = subscription_df.to_dict(orient="records") if not subscription_df.empty else []
    df.attrs["total_monthly_subscription_cost"] = float(subscription_df.attrs.get("total_monthly_subscription_cost", 0.0) or 0.0)
    return df
