// Small formatting helpers shared by components.

export const money = (x) =>
  "$" + Number(x).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// "online_gaming" -> "online gaming"
export const pretty = (s) => String(s).replace(/_/g, " ");

export const pad2 = (n) => String(n).padStart(2, "0");

// <input type="datetime-local"> wants "YYYY-MM-DDTHH:MM" in local time
export function toLocalInput(date) {
  const d = new Date(date);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}
