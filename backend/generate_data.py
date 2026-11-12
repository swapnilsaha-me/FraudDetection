"""
Generate a synthetic dataset of users and their transaction history.

Run:  python backend/generate_data.py            (defaults: 40 users, 90 days)
      python backend/generate_data.py --users 100 --days 120

Outputs:
  backend/data/users.csv         one row per user (their "normal behaviour" profile)
  backend/data/transactions.csv  labelled transactions (is_fraud = 0 / 1)

Every user has a personal spending pattern (home city, average amount, favourite
categories, active hours). Legitimate transactions follow that pattern; fraud
transactions break it in one or more ways (big amount, far away, odd hour,
risky category, rapid bursts...). The data ends at the current time so that
transactions you enter in the web app "now" continue the history naturally.
"""
import argparse
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from config import (
    CATEGORIES,
    CITIES,
    DATA_DIR,
    HIGH_RISK_CATEGORIES,
    NORMAL_CATEGORIES,
    RANDOM_SEED,
    TRANSACTIONS_CSV,
    USERS_CSV,
)

FIRST_NAMES = [
    "Ava", "Liam", "Sofia", "Noah", "Mia", "Ethan", "Isabella", "Mateo", "Emma", "Lucas",
    "Aisha", "Omar", "Priya", "Arjun", "Mei", "Chen", "Fatima", "Diego", "Grace", "Samuel",
    "Hannah", "Daniel", "Zara", "Ryan", "Lily", "Carlos", "Nora", "Elijah", "Maya", "Jacob",
    "Chloe", "Ali", "Rina", "Kevin", "Elena", "Tariq", "Julia", "Marcus", "Leah", "Victor",
]
LAST_NAMES = [
    "Garcia", "Smith", "Nguyen", "Patel", "Johnson", "Lopez", "Kim", "Brown", "Martinez", "Khan",
    "Davis", "Hernandez", "Wilson", "Rahman", "Lee", "Gonzalez", "Taylor", "Chowdhury", "Moore", "Rivera",
]

# Most users live in Texas; a few elsewhere in the US.
HOME_CITY_CHOICES = [
    "Kingsville, TX", "Kingsville, TX", "Corpus Christi, TX", "Corpus Christi, TX",
    "San Antonio, TX", "Houston, TX", "Austin, TX", "Dallas, TX", "Laredo, TX",
    "New York, NY", "Chicago, IL", "Los Angeles, CA", "Miami, FL",
]
FAR_CITIES = ["London, UK", "Lagos, Nigeria", "Moscow, Russia", "Seattle, WA",
              "Los Angeles, CA", "New York, NY", "Miami, FL", "El Paso, TX"]


def make_users(n, rng):
    users = []
    for i in range(n):
        home = rng.choice(HOME_CITY_CHOICES)
        avg = round(float(np.exp(rng.uniform(np.log(20), np.log(180)))), 2)
        start = rng.randint(6, 10)
        users.append({
            "user_id": f"U{i + 1:03d}",
            "name": f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {rng.choice(LAST_NAMES)}",
            "age": rng.randint(19, 75),
            "home_city": home,
            "avg_amount": avg,
            "std_amount": round(avg * rng.uniform(0.3, 0.6), 2),
            "usual_categories": "|".join(rng.sample(NORMAL_CATEGORIES, 3)),
            "active_start_hour": start,
            "active_end_hour": rng.randint(20, 23),
            "online_ratio": round(rng.uniform(0.05, 0.4), 2),
        })
    return users


def nearby_city(home, rng):
    """A different city within ~400 km of home (or home itself if none)."""
    from features import haversine_km
    options = [c for c in CITIES if c != home and haversine_km(home, c) < 400]
    return rng.choice(options) if options else home


def legit_txn(user, ts, rng):
    usual = user["usual_categories"].split("|")
    r = rng.random()
    if r < 0.80:
        category = rng.choice(usual)
    elif r < 0.97:
        category = rng.choice(NORMAL_CATEGORIES)
    else:
        category = rng.choice(HIGH_RISK_CATEGORIES)  # people do occasionally buy a laptop

    amount = rng.gauss(user["avg_amount"], user["std_amount"])
    if rng.random() < 0.03:  # occasional legitimately large purchase
        amount = user["avg_amount"] * rng.uniform(2.5, 6)
    amount = max(1.0, amount)

    r = rng.random()
    if r < 0.88:
        city = user["home_city"]
    elif r < 0.98:
        city = nearby_city(user["home_city"], rng)
    else:
        city = rng.choice(list(CITIES))  # a real trip

    channel = "online" if rng.random() < user["online_ratio"] else "in_store"
    return {"amount": round(amount, 2), "category": category, "city": city,
            "timestamp": ts, "channel": channel, "is_fraud": 0}


def fraud_txn(user, ts, rng):
    """A fraudulent transaction breaks the user's pattern in several (random) ways."""
    category = rng.choice(HIGH_RISK_CATEGORIES) if rng.random() < 0.7 else rng.choice(CATEGORIES)
    if rng.random() < 0.8:
        amount = user["avg_amount"] * rng.uniform(3, 20)
    else:
        amount = rng.gauss(user["avg_amount"], user["std_amount"])  # "low and slow" fraud
    city = rng.choice(FAR_CITIES) if rng.random() < 0.65 else user["home_city"]
    if rng.random() < 0.55:
        ts = ts.replace(hour=rng.randint(0, 4), minute=rng.randint(0, 59))
    channel = "online" if rng.random() < 0.7 else "in_store"
    return {"amount": round(max(1.0, amount), 2), "category": category, "city": city,
            "timestamp": ts, "channel": channel, "is_fraud": 1}


def make_transactions(user, start, end, rng):
    txns = []
    day = start
    while day < end:
        # 0-5 normal purchases per day, inside the user's active hours
        for _ in range(np.random.poisson(2.5)):
            hour = rng.randint(user["active_start_hour"], user["active_end_hour"])
            ts = day.replace(hour=hour, minute=rng.randint(0, 59), second=0)
            if ts < end:
                txns.append(legit_txn(user, ts, rng))

        # ~1.2% of days contain a fraud event; some are bursts of several charges
        if rng.random() < 0.012 * 2.5:
            ts = day.replace(hour=rng.randint(0, 23), minute=rng.randint(0, 59), second=0)
            burst = rng.choice([1, 1, 1, 2, 3, 4])
            first = fraud_txn(user, ts, rng)
            for k in range(burst):
                t = dict(first) if k == 0 else fraud_txn(user, first["timestamp"], rng)
                t["timestamp"] = first["timestamp"] + timedelta(minutes=k * rng.randint(2, 15))
                if k > 0:
                    t["city"] = first["city"]
                if t["timestamp"] < end:
                    txns.append(t)
        day += timedelta(days=1)

    txns.sort(key=lambda t: t["timestamp"])
    for t in txns:
        t["user_id"] = user["user_id"]
    return txns


def generate(num_users=40, days=90, seed=RANDOM_SEED):
    rng = random.Random(seed)
    np.random.seed(seed)

    end = datetime.now().replace(minute=0, second=0, microsecond=0)
    start = (end - timedelta(days=days)).replace(hour=0)

    users = make_users(num_users, rng)
    all_txns = []
    for u in users:
        all_txns.extend(make_transactions(u, start, end, rng))

    users_df = pd.DataFrame(users)
    txns_df = pd.DataFrame(all_txns)
    txns_df.insert(0, "transaction_id", [f"T{i + 1:06d}" for i in range(len(txns_df))])
    txns_df["timestamp"] = txns_df["timestamp"].apply(lambda t: t.isoformat(timespec="minutes"))
    txns_df = txns_df[["transaction_id", "user_id", "timestamp", "amount", "category",
                       "city", "channel", "is_fraud"]]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    users_df.to_csv(USERS_CSV, index=False)
    txns_df.to_csv(TRANSACTIONS_CSV, index=False)

    print(f"Generated {len(users_df)} users and {len(txns_df)} transactions "
          f"({txns_df['is_fraud'].sum()} fraud, {txns_df['is_fraud'].mean():.2%}).")
    print(f"  -> {USERS_CSV}\n  -> {TRANSACTIONS_CSV}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--users", type=int, default=40)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()
    generate(args.users, args.days, args.seed)
