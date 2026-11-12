// All calls to the Flask backend live here.
// Paths are relative ("/api/..."): in development Vite proxies them to Flask,
// in production Flask serves both the page and the API from the same port.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export const api = {
  meta: () => request("/api/meta"),
  users: () => request("/api/users"),
  user: (userId) => request(`/api/users/${userId}`),
  model: () => request("/api/model"),
  predict: (txn) => request("/api/predict", { method: "POST", body: JSON.stringify(txn) }),
  reset: () => request("/api/reset", { method: "POST" }),
};
