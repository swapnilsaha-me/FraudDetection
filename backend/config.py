"""
Shared constants for the whole backend.

Edit this file to change cities, merchant categories, file locations,
or the fraud decision threshold.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# File locations
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"   # React production build (created by `npm run build`)

DATA_DIR = BACKEND_DIR / "data"
MODEL_DIR = BACKEND_DIR / "model"

USERS_CSV = DATA_DIR / "users.csv"                 # user profiles (generated)
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"   # labelled history used for training
APP_TRANSACTIONS_CSV = DATA_DIR / "app_transactions.csv"  # transactions entered in the web app

MODEL_PATH = MODEL_DIR / "fraud_model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

# ---------------------------------------------------------------------------
# Server (localhost only). Port 5000 is used by AirPlay on macOS, so we use 5050.
# ---------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 5050

# ---------------------------------------------------------------------------
# Model settings
# ---------------------------------------------------------------------------
# If the predicted fraud probability is >= this value, the transaction is flagged.
FRAUD_THRESHOLD = 0.5
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Domain values
# ---------------------------------------------------------------------------
# City name -> (latitude, longitude)
CITIES = {
    "Kingsville, TX": (27.5159, -97.8561),
    "Corpus Christi, TX": (27.8006, -97.3964),
    "San Antonio, TX": (29.4241, -98.4936),
    "Houston, TX": (29.7604, -95.3698),
    "Austin, TX": (30.2672, -97.7431),
    "Dallas, TX": (32.7767, -96.7970),
    "Laredo, TX": (27.5306, -99.4803),
    "El Paso, TX": (31.7619, -106.4850),
    "New York, NY": (40.7128, -74.0060),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Chicago, IL": (41.8781, -87.6298),
    "Miami, FL": (25.7617, -80.1918),
    "Seattle, WA": (47.6062, -122.3321),
    "Denver, CO": (39.7392, -104.9903),
    "London, UK": (51.5074, -0.1278),
    "Lagos, Nigeria": (6.5244, 3.3792),
    "Moscow, Russia": (55.7558, 37.6173),
}

# Everyday categories most users spend on.
NORMAL_CATEGORIES = [
    "grocery",
    "restaurant",
    "gas",
    "retail",
    "entertainment",
    "health",
    "utilities",
]

# Categories fraudsters prefer (easy to resell / hard to trace).
HIGH_RISK_CATEGORIES = [
    "electronics",
    "jewelry",
    "online_gaming",
    "travel",
    "gift_cards",
]

CATEGORIES = NORMAL_CATEGORIES + HIGH_RISK_CATEGORIES

CHANNELS = ["in_store", "online"]
