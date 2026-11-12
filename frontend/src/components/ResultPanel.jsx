export default function ResultPanel({ result }) {
  const { is_fraud, fraud_probability: p, threshold, reasons, features } = result;
  const pct = (x) => (x * 100).toFixed(1) + "%";

  return (
    <div className="result">
      <div className={`verdict ${is_fraud ? "bad" : "ok"}`}>
        {is_fraud ? "⚠️ FRAUD SUSPECTED" : "✅ Looks legitimate"}
      </div>

      <div className="prob">
        <div className="prob-label">
          Fraud probability: <strong>{pct(p)}</strong>{" "}
          <span className="muted">(flagged at ≥ {(threshold * 100).toFixed(0)}%)</span>
        </div>
        <div className="bar">
          <div className="bar-fill"
               style={{ width: pct(p), background: is_fraud ? "var(--bad)" : "var(--ok)" }} />
          <div className="bar-mark" style={{ left: threshold * 100 + "%" }} />
        </div>
      </div>

      <h3>Why?</h3>
      <ul className="reasons">
        {reasons.map((r) => <li key={r}>{r}</li>)}
      </ul>

      <details>
        <summary>Features sent to the model</summary>
        <pre>{JSON.stringify(features, null, 2)}</pre>
      </details>
    </div>
  );
}
