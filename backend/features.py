"""
Feature engineering.

The SAME function (`build_features`) is used both when training the model and
when the web app scores a new transaction. Keeping it in one place guarantees
the model always sees features computed the same way.

To add a new feature:
  1. compute it inside `build_features`
  2. add its name to FEATURE_COLUMNS
  3. retrain:  python backend/train_model.py
"""
import math
from datetime import datetime, timedelta

from config import CATEGORIES, CITIES, HIGH_RISK_CATEGORIES

FEATURE_COLUMNS = [
    "amount",
    "amount_ratio",            # amount / user's average amount
    "amount_zscore",           # (amount - avg) / std
    "distance_from_home_km",
    "distance_from_last_km",   # distance from the user's previous transaction
    "travel_speed_kmh",        # implied speed between previous and current location
    "txn_count_last_1h",
    "txn_count_last_24h",
    "hour",
    "is_night",                # 00:00 - 04:59
    "outside_active_hours",    # outside this user's normal shopping hours
    "is_online",
    "is_usual_category",       # category is one of the user's favourites
    "is_high_risk_category",
] + ["cat_" + c for c in CATEGORIES]


def haversine_km(city_a, city_b):
    """Great-circle distance in km between two city names from config.CITIES."""
    lat1, lon1 = CITIES[city_a]
    lat2, lon2 = CITIES[city_b]
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parse_time(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def usual_categories(user):
    """users.csv stores favourite categories as 'grocery|gas|restaurant'."""
    return str(user["usual_categories"]).split("|")


def build_features(user, txn, history):
    """
    Build the feature dictionary for one transaction.

    user    : dict with the user's profile (a row of users.csv)
    txn     : dict with keys amount, category, city, timestamp, channel
    history : list of the user's PREVIOUS transactions (dicts with timestamp, city),
              sorted oldest -> newest. Only entries before txn's timestamp are used.
    """
    ts = parse_time(txn["timestamp"])
    amount = float(txn["amount"])
    category = txn["category"]
    city = txn["city"]

    avg = float(user["avg_amount"])
    std = max(float(user["std_amount"]), 1.0)

    past = [h for h in history if parse_time(h["timestamp"]) < ts]

    # --- velocity / location features based on the previous transaction ---
    if past:
        last = past[-1]
        dist_last = haversine_km(last["city"], city)
        hours_gap = max((ts - parse_time(last["timestamp"])).total_seconds() / 3600.0, 1 / 60)
        speed = dist_last / hours_gap
    else:
        dist_last, speed = 0.0, 0.0

    one_hour_ago = ts - timedelta(hours=1)
    one_day_ago = ts - timedelta(hours=24)
    count_1h = sum(1 for h in past if parse_time(h["timestamp"]) >= one_hour_ago)
    count_24h = sum(1 for h in past if parse_time(h["timestamp"]) >= one_day_ago)

    hour = ts.hour
    start, end = int(user["active_start_hour"]), int(user["active_end_hour"])

    features = {
        "amount": amount,
        "amount_ratio": amount / max(avg, 1.0),
        "amount_zscore": (amount - avg) / std,
        "distance_from_home_km": haversine_km(user["home_city"], city),
        "distance_from_last_km": dist_last,
        "travel_speed_kmh": min(speed, 20000.0),
        "txn_count_last_1h": count_1h,
        "txn_count_last_24h": count_24h,
        "hour": hour,
        "is_night": int(hour < 5),
        "outside_active_hours": int(not (start <= hour <= end)),
        "is_online": int(txn["channel"] == "online"),
        "is_usual_category": int(category in usual_categories(user)),
        "is_high_risk_category": int(category in HIGH_RISK_CATEGORIES),
    }
    for c in CATEGORIES:
        features["cat_" + c] = int(category == c)
    return features


def explain(user, txn, features):
    """
    Human-readable reasons shown in the UI.
    These are simple rules on top of the features (the model itself decides
    the verdict; this just tells the user what looks unusual).
    """
    reasons = []
    avg = float(user["avg_amount"])
    if features["amount_ratio"] >= 3:
        reasons.append(
            f"Amount ${features['amount']:,.2f} is {features['amount_ratio']:.1f}x this user's average (${avg:,.2f})."
        )
    if features["distance_from_home_km"] > 300:
        reasons.append(
            f"Location is {features['distance_from_home_km']:,.0f} km from the user's home city ({user['home_city']})."
        )
    if features["travel_speed_kmh"] > 900:
        reasons.append(
            f"Impossible travel: would require moving {features['travel_speed_kmh']:,.0f} km/h since the previous transaction."
        )
    if features["txn_count_last_1h"] >= 3:
        reasons.append(f"{features['txn_count_last_1h']} other transactions in the past hour (rapid burst).")
    if features["is_night"]:
        reasons.append(f"Made in the middle of the night (hour {features['hour']:02d}:00).")
    elif features["outside_active_hours"]:
        reasons.append(
            f"Outside the user's normal shopping hours ({int(user['active_start_hour']):02d}:00-{int(user['active_end_hour']):02d}:00)."
        )
    if features["is_high_risk_category"]:
        reasons.append(f"'{txn['category']}' is a high-risk merchant category.")
    elif not features["is_usual_category"]:
        reasons.append(f"'{txn['category']}' is not one of this user's usual categories.")
    if features["is_online"] and features["amount_ratio"] >= 3:
        reasons.append("Large online (card-not-present) purchase.")
    if not reasons:
        reasons.append("Transaction matches this user's normal spending behaviour.")
    return reasons
