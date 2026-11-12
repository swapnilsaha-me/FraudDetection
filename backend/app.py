"""
Flask web server: serves the frontend and a small JSON API.

Run:  python backend/app.py      then open http://127.0.0.1:5050

The page itself is the React app in frontend/. Flask serves its production
build (frontend/dist, created with `npm run build`). During development you
can instead run `npm run dev` in frontend/ and open http://localhost:5173.

On first start it automatically generates the dataset and trains the model
if they are missing.

API
  GET  /api/meta                  cities, categories, channels, threshold
  GET  /api/users                 list of users (id, name, home city)
  GET  /api/users/<user_id>       profile + 15 most recent transactions
  POST /api/predict               score a transaction (and save it to history)
  POST /api/reset                 delete all transactions entered through the app
  GET  /api/model                 model evaluation metrics
"""
import csv
import json
from datetime import datetime

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from config import (
    APP_TRANSACTIONS_CSV,
    CATEGORIES,
    CHANNELS,
    CITIES,
    FRAUD_THRESHOLD,
    FRONTEND_DIST,
    HOST,
    METRICS_PATH,
    MODEL_PATH,
    PORT,
    TRANSACTIONS_CSV,
    USERS_CSV,
)
from features import FEATURE_COLUMNS, build_features, explain

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")

TXN_FIELDS = ["transaction_id", "user_id", "timestamp", "amount", "category",
              "city", "channel", "is_fraud", "fraud_probability", "source"]

# In-memory state, filled by load_state()
USERS = {}      # user_id -> profile dict
HISTORY = {}    # user_id -> list of transaction dicts (oldest -> newest)
MODEL = None


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
def ensure_data_and_model():
    if not USERS_CSV.exists() or not TRANSACTIONS_CSV.exists():
        print("No dataset found - generating one...")
        from generate_data import generate
        generate()
    if not MODEL_PATH.exists():
        print("No trained model found - training one...")
        from train_model import train
        train()


def load_state():
    global MODEL
    USERS.clear()
    HISTORY.clear()

    users_df = pd.read_csv(USERS_CSV)
    for u in users_df.to_dict("records"):
        USERS[u["user_id"]] = u
        HISTORY[u["user_id"]] = []

    frames = [pd.read_csv(TRANSACTIONS_CSV).assign(source="dataset", fraud_probability=None)]
    if APP_TRANSACTIONS_CSV.exists():
        frames.append(pd.read_csv(APP_TRANSACTIONS_CSV))
    txns = pd.concat(frames, ignore_index=True).sort_values("timestamp")
    txns = txns.astype(object).where(txns.notna(), None)
    for t in txns.to_dict("records"):
        if t["user_id"] in HISTORY:
            HISTORY[t["user_id"]].append(t)

    bundle = joblib.load(MODEL_PATH)
    if bundle["features"] != FEATURE_COLUMNS:
        raise RuntimeError("Model was trained with different features. Run: python backend/train_model.py")
    MODEL = bundle["model"]


def save_app_transaction(txn):
    new_file = not APP_TRANSACTIONS_CSV.exists()
    with open(APP_TRANSACTIONS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TXN_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({k: txn.get(k) for k in TXN_FIELDS})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if not (FRONTEND_DIST / "index.html").exists():
        return (
            "<h2>Frontend not built yet</h2>"
            "<p>Run <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>, then refresh.</p>"
            "<p>Or for development: <code>cd frontend &amp;&amp; npm run dev</code> and open "
            "<a href='http://localhost:5173'>http://localhost:5173</a>.</p>"
        ), 200
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/api/meta")
def meta():
    return jsonify({
        "cities": list(CITIES),
        "categories": CATEGORIES,
        "channels": CHANNELS,
        "threshold": FRAUD_THRESHOLD,
    })


@app.get("/api/users")
def list_users():
    return jsonify([
        {"user_id": u["user_id"], "name": u["name"], "home_city": u["home_city"]}
        for u in USERS.values()
    ])


@app.get("/api/users/<user_id>")
def get_user(user_id):
    user = USERS.get(user_id)
    if user is None:
        return jsonify({"error": f"Unknown user {user_id}"}), 404
    history = HISTORY[user_id]
    return jsonify({
        "profile": {**user, "usual_categories": user["usual_categories"].split("|")},
        "stats": {
            "total_transactions": len(history),
            "fraud_transactions": sum(int(t["is_fraud"] or 0) for t in history),
        },
        "recent_transactions": list(reversed(history[-15:])),
    })


@app.post("/api/predict")
def predict():
    data = request.get_json(force=True) or {}

    # ---- validate input ----
    user = USERS.get(data.get("user_id"))
    if user is None:
        return jsonify({"error": "Please select a valid user."}), 400
    try:
        amount = float(data.get("amount"))
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a positive number."}), 400
    if data.get("category") not in CATEGORIES:
        return jsonify({"error": "Unknown category."}), 400
    if data.get("city") not in CITIES:
        return jsonify({"error": "Unknown city."}), 400
    if data.get("channel") not in CHANNELS:
        return jsonify({"error": "Unknown channel."}), 400
    try:
        ts = datetime.fromisoformat(data.get("timestamp") or datetime.now().isoformat())
    except ValueError:
        return jsonify({"error": "Invalid date/time."}), 400

    txn = {
        "user_id": user["user_id"],
        "timestamp": ts.isoformat(timespec="minutes"),
        "amount": round(amount, 2),
        "category": data["category"],
        "city": data["city"],
        "channel": data["channel"],
    }

    # ---- run the model ----
    history = HISTORY[user["user_id"]]
    features = build_features(user, txn, history)
    X = pd.DataFrame([features])[FEATURE_COLUMNS]
    probability = float(MODEL.predict_proba(X)[0, 1])
    is_fraud = probability >= FRAUD_THRESHOLD

    # ---- save to history so later transactions see it (velocity features) ----
    txn.update({
        "transaction_id": "A" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "is_fraud": int(is_fraud),
        "fraud_probability": round(probability, 4),
        "source": "app",
    })
    if data.get("save", True):
        history.append(txn)
        history.sort(key=lambda t: t["timestamp"])
        save_app_transaction(txn)

    return jsonify({
        "transaction": txn,
        "is_fraud": bool(is_fraud),
        "fraud_probability": round(probability, 4),
        "threshold": FRAUD_THRESHOLD,
        "reasons": explain(user, txn, features),
        "features": features,
    })


@app.post("/api/reset")
def reset():
    if APP_TRANSACTIONS_CSV.exists():
        APP_TRANSACTIONS_CSV.unlink()
    load_state()
    return jsonify({"ok": True})


@app.get("/api/model")
def model_info():
    if not METRICS_PATH.exists():
        return jsonify({"error": "No metrics found. Train the model first."}), 404
    return jsonify(json.loads(METRICS_PATH.read_text()))


if __name__ == "__main__":
    ensure_data_and_model()
    load_state()
    print(f"\nFraud Detection app running at  http://{HOST}:{PORT}\n")
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)
