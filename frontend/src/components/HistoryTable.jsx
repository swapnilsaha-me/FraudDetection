import { money, pretty } from "../utils.js";

export default function HistoryTable({ rows, highlightId }) {
  let body;
  if (!rows) {
    body = <EmptyRow text="Select a user to see history." />;
  } else if (rows.length === 0) {
    body = <EmptyRow text="No transactions." />;
  } else {
    body = rows.map((t) => {
      const fraud = Number(t.is_fraud) === 1;
      return (
        <tr key={t.transaction_id} className={t.transaction_id === highlightId ? "new-row" : ""}>
          <td>{t.timestamp.replace("T", " ")}</td>
          <td>{money(t.amount)}</td>
          <td>{pretty(t.category)}</td>
          <td>{t.city}</td>
          <td>{pretty(t.channel)}</td>
          <td>
            <span className={`badge ${fraud ? "bad" : "ok"}`}>{fraud ? "Fraud" : "Legit"}</span>
            {t.source === "app" && (
              <span className="muted" title="Entered in the app (label = model prediction)"> app</span>
            )}
          </td>
        </tr>
      );
    });
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Amount</th><th>Category</th><th>City</th><th>Channel</th><th>Status</th>
          </tr>
        </thead>
        <tbody>{body}</tbody>
      </table>
    </div>
  );
}

function EmptyRow({ text }) {
  return (
    <tr>
      <td colSpan={6} className="muted">{text}</td>
    </tr>
  );
}
