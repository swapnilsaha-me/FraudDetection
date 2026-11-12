import { useEffect, useState } from "react";
import { api } from "../api.js";
import { pretty } from "../utils.js";

export default function ModelInfo({ onReset }) {
  const [m, setM] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.model().then(setM).catch((e) => setError(e.message));
  }, []);

  function handleReset() {
    if (confirm("Delete every transaction entered through the app? (The original dataset is kept.)")) {
      onReset().catch((e) => setError(e.message));
    }
  }

  const pct = (x) => (x * 100).toFixed(1) + "%";

  return (
    <footer className="card model-info">
      <h2>Model</h2>
      {error && <div className="muted">{error}</div>}
      {!m && !error && <div className="muted">Loading model info…</div>}
      {m && (
        <div className="muted">
          <p>
            {m.model} trained {m.trained_at.replace("T", " ")} on {m.n_train} transactions,
            evaluated on {m.n_test} held-out transactions.
          </p>
          <div className="metrics">
            <Metric value={pct(m.accuracy)} label="Accuracy" />
            <Metric value={pct(m.precision)} label="Precision" />
            <Metric value={pct(m.recall)} label="Recall" />
            <Metric value={pct(m.f1)} label="F1 score" />
            <Metric value={m.roc_auc.toFixed(3)} label="ROC AUC" />
            <Metric value={`${m.confusion_matrix.tp} / ${m.confusion_matrix.fn}`} label="Fraud caught / missed" />
            <Metric value={m.confusion_matrix.fp} label="False alarms" />
          </div>
          <p>
            Most important features:{" "}
            {m.top_features.slice(0, 5).map((f) => pretty(f.feature)).join(", ")}.
          </p>
        </div>
      )}
      <button type="button" className="link" onClick={handleReset}>
        Clear transactions entered in the app
      </button>
    </footer>
  );
}

function Metric({ value, label }) {
  return (
    <div>
      <strong>{value}</strong>
      {label}
    </div>
  );
}
