import { money, pad2, pretty } from "../utils.js";
import HistoryTable from "./HistoryTable.jsx";

export default function UserPanel({ users, userId, userData, highlightId, onSelect }) {
  const p = userData?.profile;

  return (
    <section className="card">
      <h2>1. Select a user</h2>
      <select value={userId} onChange={(e) => onSelect(e.target.value)}>
        <option value="">{users.length ? "-- choose a user --" : "Loading users…"}</option>
        {users.map((u) => (
          <option key={u.user_id} value={u.user_id}>
            {u.user_id} · {u.name} ({u.home_city})
          </option>
        ))}
      </select>

      {p && (
        <div className="profile">
          <div className="profile-grid">
            <Field label="Home city">{p.home_city}</Field>
            <Field label="Age">{p.age}</Field>
            <Field label="Average spend">
              {money(p.avg_amount)} ± {money(p.std_amount)}
            </Field>
            <Field label="Active hours">
              {pad2(p.active_start_hour)}:00 – {pad2(p.active_end_hour)}:59
            </Field>
            <Field label="Online purchases">{Math.round(p.online_ratio * 100)}%</Field>
            <Field label="History">
              {userData.stats.total_transactions} txns · {userData.stats.fraud_transactions} fraud
            </Field>
          </div>
          <span className="label">Usual categories</span>
          <div className="chips">
            {p.usual_categories.map((c) => (
              <span key={c} className="chip">{pretty(c)}</span>
            ))}
          </div>
        </div>
      )}

      <h3>Recent transactions</h3>
      <HistoryTable rows={userData?.recent_transactions} highlightId={highlightId} />
    </section>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <span className="label">{label}</span>
      <span>{children}</span>
    </div>
  );
}
