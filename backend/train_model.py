"""
Train the fraud detection model.

Run:  python backend/train_model.py

Steps:
  1. load users.csv + transactions.csv
  2. build features for every transaction (using only that user's earlier history)
  3. split 80% train / 20% test (stratified, so both sets contain fraud)
  4. train a Random Forest classifier
  5. print + save evaluation metrics, and save the model to backend/model/

Want to try another algorithm? Change `make_model()` below - anything with
fit / predict_proba from scikit-learn works (e.g. GradientBoostingClassifier,
LogisticRegression inside a Pipeline with StandardScaler).
"""
import json
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from config import FRAUD_THRESHOLD, METRICS_PATH, MODEL_DIR, MODEL_PATH, RANDOM_SEED, TRANSACTIONS_CSV, USERS_CSV
from features import FEATURE_COLUMNS, build_features


def make_model():
    return RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",  # fraud is rare -> give it more weight
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )


def build_dataset():
    users = pd.read_csv(USERS_CSV).set_index("user_id").to_dict("index")
    txns = pd.read_csv(TRANSACTIONS_CSV).sort_values(["user_id", "timestamp"])

    rows, labels = [], []
    for user_id, group in txns.groupby("user_id"):
        user = users[user_id]
        history = []
        for t in group.to_dict("records"):
            rows.append(build_features(user, t, history))
            labels.append(int(t["is_fraud"]))
            history.append(t)
    return pd.DataFrame(rows)[FEATURE_COLUMNS], pd.Series(labels, name="is_fraud")


def train():
    print("Building features...")
    X, y = build_dataset()
    print(f"  {len(X)} transactions, {int(y.sum())} fraud ({y.mean():.2%})")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_SEED
    )

    print("Training Random Forest...")
    model = make_model()
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= FRAUD_THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()

    importances = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_), key=lambda x: x[1], reverse=True
    )
    metrics = {
        "model": type(model).__name__,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "threshold": FRAUD_THRESHOLD,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "accuracy": round(accuracy_score(y_test, pred), 4),
        "precision": round(precision_score(y_test, pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, proba), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "top_features": [{"feature": f, "importance": round(float(i), 4)} for f, i in importances[:10]],
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLUMNS}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    print("\nTest-set results")
    for k in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
        print(f"  {k:<10} {metrics[k]}")
    print(f"  confusion  TN={tn} FP={fp} FN={fn} TP={tp}")
    print("\nTop features")
    for f in metrics["top_features"]:
        print(f"  {f['feature']:<24} {f['importance']}")
    print(f"\nSaved model -> {MODEL_PATH}")


if __name__ == "__main__":
    train()
