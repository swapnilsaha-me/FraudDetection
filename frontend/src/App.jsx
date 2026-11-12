// Top-level component: holds the shared state and lays out the page.
//
//   App
//   ├── UserPanel         pick a user, see profile
//   │   └── HistoryTable  recent transactions
//   ├── TransactionForm   enter a transaction
//   ├── ResultPanel       verdict, probability, reasons
//   └── ModelInfo         model metrics + reset button

import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import UserPanel from "./components/UserPanel.jsx";
import TransactionForm from "./components/TransactionForm.jsx";
import ResultPanel from "./components/ResultPanel.jsx";
import ModelInfo from "./components/ModelInfo.jsx";

export default function App() {
  const [meta, setMeta] = useState(null);         // cities, categories, channels, threshold
  const [users, setUsers] = useState([]);
  const [userId, setUserId] = useState("");
  const [userData, setUserData] = useState(null); // { profile, stats, recent_transactions }
  const [result, setResult] = useState(null);     // last prediction
  const [highlightId, setHighlightId] = useState(null);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState(
    () => document.documentElement.dataset.theme === "dark" ? "dark" : "light"
  );

  // Apply the theme to <html> and remember the choice.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch { /* storage unavailable */ }
  }, [theme]);

  // Load dropdown options and the user list once on start-up.
  useEffect(() => {
    Promise.all([api.meta(), api.users()])
      .then(([m, u]) => {
        setMeta(m);
        setUsers(u);
      })
      .catch((e) =>
        setError(`Could not reach the backend. Is "python backend/app.py" running? (${e.message})`)
      );
  }, []);

  const loadUser = useCallback(async (id) => {
    if (!id) {
      setUserData(null);
      return;
    }
    setUserData(await api.user(id));
  }, []);

  function selectUser(id) {
    setUserId(id);
    setResult(null);
    setHighlightId(null);
    setError("");
    loadUser(id).catch((e) => setError(e.message));
  }

  async function checkTransaction(txn) {
    setError("");
    const r = await api.predict({ user_id: userId, ...txn });
    setResult(r);
    setHighlightId(r.transaction.transaction_id);
    await loadUser(userId); // refresh history so the new transaction appears
  }

  async function resetAppTransactions() {
    await api.reset();
    setResult(null);
    setHighlightId(null);
    await loadUser(userId);
  }

  return (
    <>
      <header className="topbar">
        <h1>🛡️ Transaction Fraud Detection</h1>
        <span className="subtitle">Machine-learning powered · runs on localhost</span>
        <button
          type="button"
          className="theme-toggle"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? "☀️ Light" : "🌙 Night"}
        </button>
      </header>

      <main className="layout">
        <UserPanel
          users={users}
          userId={userId}
          userData={userData}
          highlightId={highlightId}
          onSelect={selectUser}
        />

        <section className="card">
          <h2>2. Enter a transaction</h2>
          {meta && (
            <TransactionForm
              meta={meta}
              profile={userData?.profile}
              onSubmit={checkTransaction}
              onError={setError}
            />
          )}
          {result && <ResultPanel result={result} />}
          {error && <div className="error">{error}</div>}
        </section>
      </main>

      <ModelInfo onReset={resetAppTransactions} />
    </>
  );
}
