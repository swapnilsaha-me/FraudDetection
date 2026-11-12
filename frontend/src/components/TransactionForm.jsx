import { useState } from "react";
import { pretty, toLocalInput } from "../utils.js";

export default function TransactionForm({ meta, profile, onSubmit, onError }) {
  const [form, setForm] = useState({
    amount: "",
    category: meta.categories[0],
    city: meta.cities[0],
    timestamp: toLocalInput(new Date()),
    channel: meta.channels[0],
  });
  const [busy, setBusy] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  // ---- example buttons ----
  function fillNormal() {
    if (!profile) return onError("Select a user first.");
    onError("");
    const d = new Date();
    d.setHours(Math.min(Math.max(d.getHours(), profile.active_start_hour), profile.active_end_hour), 15);
    const cats = profile.usual_categories;
    setForm({
      amount: (profile.avg_amount * (0.7 + Math.random() * 0.6)).toFixed(2),
      category: cats[Math.floor(Math.random() * cats.length)],
      city: profile.home_city,
      timestamp: toLocalInput(d),
      channel: "in_store",
    });
  }

  function fillSuspicious() {
    if (!profile) return onError("Select a user first.");
    onError("");
    const d = new Date();
    d.setHours(3, 12);
    setForm({
      amount: (profile.avg_amount * 12).toFixed(2),
      category: "electronics",
      city: profile.home_city.includes("TX") ? "Lagos, Nigeria" : "Moscow, Russia",
      timestamp: toLocalInput(d),
      channel: "online",
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!profile) return onError("Select a user first.");
    setBusy(true);
    try {
      await onSubmit(form);
    } catch (err) {
      onError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Amount (USD)
        <input type="number" min="0.01" step="0.01" placeholder="e.g. 45.99" required
               value={form.amount} onChange={update("amount")} />
      </label>
      <label>
        Merchant category
        <select value={form.category} onChange={update("category")}>
          {meta.categories.map((c) => <option key={c} value={c}>{pretty(c)}</option>)}
        </select>
      </label>
      <label>
        Location (city)
        <select value={form.city} onChange={update("city")}>
          {meta.cities.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </label>
      <label>
        Date &amp; time
        <input type="datetime-local" required value={form.timestamp} onChange={update("timestamp")} />
      </label>
      <label>
        Channel
        <select value={form.channel} onChange={update("channel")}>
          {meta.channels.map((c) => <option key={c} value={c}>{pretty(c)}</option>)}
        </select>
      </label>

      <div className="buttons">
        <button type="submit" className="primary" disabled={busy}>
          {busy ? "Checking…" : "Check transaction"}
        </button>
        <button type="button" onClick={fillNormal}>Fill normal example</button>
        <button type="button" onClick={fillSuspicious}>Fill suspicious example</button>
      </div>
    </form>
  );
}
