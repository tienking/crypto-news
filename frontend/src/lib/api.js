const BASE = "/api/crypto-news";

export async function fetchArticles({ page = 1, limit = 24, source = "", q = "" } = {}) {
  const params = new URLSearchParams({ page, limit });
  if (source) params.set("source", source);
  if (q) params.set("q", q);
  const res = await fetch(`${BASE}/articles?${params}`);
  if (!res.ok) throw new Error("Failed to load articles");
  return res.json();
}

export async function fetchArticle(id) {
  const res = await fetch(`${BASE}/article/${id}`);
  if (!res.ok) throw new Error("Article not found");
  return res.json();
}

export async function fetchSources() {
  const res = await fetch(`${BASE}/sources`);
  if (!res.ok) return [];
  return res.json();
}

export async function chat(message, history) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error("Chat request failed");
  return res.json(); // { reply }
}

export async function fetchCoins() {
  const res = await fetch(`${BASE}/coins`);
  if (!res.ok) return [];
  return res.json();
}

// ── Admin ──────────────────────────────────────────────────────────────────────

const authH = (token) => ({ "Content-Type": "application/json", Authorization: `Bearer ${token}` });

export async function adminLogin(username, password) {
  const res = await fetch(`${BASE}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Invalid username or password");
  return res.json(); // { access_token }
}

export async function adminGetCoins(token) {
  const res = await fetch(`${BASE}/admin/coins`, { headers: authH(token) });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

export async function adminSaveCoins(token, items) {
  const res = await fetch(`${BASE}/admin/coins`, { method: "PUT", headers: authH(token), body: JSON.stringify({ items }) });
  if (!res.ok) throw new Error("Save failed");
  return res.json();
}

export async function adminGetFeeds(token) {
  const res = await fetch(`${BASE}/admin/feeds`, { headers: authH(token) });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

export async function adminSaveFeeds(token, items) {
  const res = await fetch(`${BASE}/admin/feeds`, { method: "PUT", headers: authH(token), body: JSON.stringify({ items }) });
  if (!res.ok) throw new Error("Save failed");
  return res.json();
}

// "3h ago", "2d ago", etc.
export function timeAgo(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
