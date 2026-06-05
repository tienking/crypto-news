import { useState, useEffect } from "react";
import { adminLogin, adminGetCoins, adminSaveCoins, adminGetFeeds, adminSaveFeeds } from "./lib/api";

const NEWS_URL = "/projects/crypto-news/";

function getToken() {
  const t = localStorage.getItem("cn_admin_token");
  if (!t) return null;
  try {
    const p = JSON.parse(atob(t.split(".")[1]));
    if (p.exp * 1000 < Date.now()) { localStorage.removeItem("cn_admin_token"); return null; }
    return t;
  } catch { localStorage.removeItem("cn_admin_token"); return null; }
}

const inp = {
  fontSize: 13, padding: "8px 11px", borderRadius: 8, border: "1px solid var(--border)",
  background: "var(--bg)", color: "var(--text)", outline: "none", fontFamily: "var(--font-display)",
  boxSizing: "border-box", width: "100%",
};

// ── Login ───────────────────────────────────────────────────────────────────────

function Login({ onLogin }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      const { access_token } = await adminLogin(u, p);
      localStorage.setItem("cn_admin_token", access_token);
      onLogin(access_token);
    } catch { setErr("Invalid username or password."); }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div style={{ width: 340, background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 16, padding: "32px 28px" }}>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent)", letterSpacing: "0.12em", marginBottom: 8 }}>CRYPTO NEWS · ADMIN</p>
        <h1 style={{ fontSize: 21, fontWeight: 800, marginBottom: 22 }}>Sign in</h1>
        <form onSubmit={submit}>
          <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 5 }}>Username</label>
          <input value={u} onChange={e => setU(e.target.value)} required autoFocus style={{ ...inp, marginBottom: 14 }} />
          <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 5 }}>Password</label>
          <input type="password" value={p} onChange={e => setP(e.target.value)} required style={{ ...inp, marginBottom: err ? 10 : 20 }} />
          {err && <p style={{ fontSize: 12, color: "#f87171", marginBottom: 14 }}>{err}</p>}
          <button type="submit" disabled={loading}
            style={{ width: "100%", padding: 10, borderRadius: 9, border: "none", background: "var(--accent)", color: "#000", fontSize: 13, fontWeight: 700, cursor: loading ? "default" : "pointer", opacity: loading ? 0.7 : 1 }}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <a href={NEWS_URL} style={{ display: "inline-block", marginTop: 16, fontSize: 12, color: "var(--text-muted)", textDecoration: "none" }}>← Back to news</a>
      </div>
    </div>
  );
}

// ── Generic 2-field list editor ──────────────────────────────────────────────────

function ListEditor({ title, fields, items, setItems }) {
  const update = (i, key, val) => setItems(items.map((it, idx) => idx === i ? { ...it, [key]: val } : it));
  const remove = (i) => setItems(items.filter((_, idx) => idx !== i));
  const add = () => setItems([...items, Object.fromEntries(fields.map(f => [f.key, ""]))]);

  return (
    <div>
      <h2 style={{ fontSize: 13, fontFamily: "var(--font-mono)", color: "var(--text-muted)", letterSpacing: "0.06em", marginBottom: 12 }}>{title}</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {items.map((it, i) => (
          <div key={i} style={{ display: "grid", gridTemplateColumns: fields.map(f => f.w).join(" ") + " auto", gap: 8, alignItems: "center" }}>
            {fields.map(f => (
              <input key={f.key} value={it[f.key] || ""} placeholder={f.placeholder}
                onChange={e => update(i, f.key, e.target.value)}
                style={{ ...inp, fontFamily: f.mono ? "var(--font-mono)" : "var(--font-display)" }} />
            ))}
            <button onClick={() => remove(i)} title="Remove"
              style={{ width: 30, height: 30, borderRadius: 7, border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.08)", color: "#f87171", cursor: "pointer", fontSize: 13 }}>✕</button>
          </div>
        ))}
      </div>
      <button onClick={add}
        style={{ marginTop: 10, width: "100%", padding: 9, borderRadius: 9, border: "1px dashed var(--border)", background: "none", color: "var(--text-muted)", fontSize: 13, cursor: "pointer", fontFamily: "var(--font-display)" }}>
        + Add
      </button>
    </div>
  );
}

// ── Dashboard ────────────────────────────────────────────────────────────────────

function Dashboard({ token, onLogout }) {
  const [coins, setCoins] = useState([]);
  const [feeds, setFeeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingCoins, setSavingCoins] = useState(false);
  const [savingFeeds, setSavingFeeds] = useState(false);
  const [msg, setMsg] = useState("");

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(""), 3000); };

  useEffect(() => {
    Promise.all([adminGetCoins(token), adminGetFeeds(token)])
      .then(([c, f]) => { setCoins(c); setFeeds(f); setLoading(false); })
      .catch(() => { localStorage.removeItem("cn_admin_token"); onLogout(); });
  }, [token]);

  const saveCoins = async () => {
    setSavingCoins(true);
    try { await adminSaveCoins(token, coins.filter(c => c.label && c.symbol)); flash("✓ Coins saved"); }
    catch { flash("Failed to save coins"); }
    setSavingCoins(false);
  };

  const saveFeeds = async () => {
    setSavingFeeds(true);
    try {
      const res = await adminSaveFeeds(token, feeds.filter(f => f.name && f.url));
      flash(`✓ Feeds saved · fetched ${res.fetched}, +${res.inserted} new`);
    } catch { flash("Failed to save feeds"); }
    setSavingFeeds(false);
  };

  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div style={{ width: 26, height: 26, borderRadius: "50%", border: "2px solid var(--accent)", borderTopColor: "transparent", animation: "spin .8s linear infinite" }} />
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text)" }}>
      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-surface)" }}>
        <div style={{ maxWidth: 860, margin: "0 auto", padding: "14px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--accent)", letterSpacing: "0.1em" }}>CN ADMIN</p>
            <span style={{ color: "var(--border)" }}>·</span>
            <p style={{ fontSize: 14, fontWeight: 600 }}>Crypto News</p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {msg && <span style={{ fontSize: 12, color: "var(--accent)", fontFamily: "var(--font-mono)" }}>{msg}</span>}
            <a href={NEWS_URL} style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "none" }}>View site →</a>
            <button onClick={onLogout} style={{ fontSize: 12, color: "var(--text-muted)", background: "none", border: "1px solid var(--border)", borderRadius: 8, padding: "5px 12px", cursor: "pointer", fontFamily: "var(--font-display)" }}>Sign out</button>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 860, margin: "0 auto", padding: "28px 24px 60px", display: "flex", flexDirection: "column", gap: 40 }}>
        {/* Coins */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>Chart coin pairs</h1>
            <button onClick={saveCoins} disabled={savingCoins}
              style={{ padding: "8px 20px", borderRadius: 9, border: "none", background: "var(--accent)", color: "#000", fontSize: 13, fontWeight: 700, cursor: savingCoins ? "default" : "pointer", opacity: savingCoins ? 0.7 : 1 }}>
              {savingCoins ? "Saving..." : "Save"}
            </button>
          </div>
          <ListEditor title="LABEL · TRADINGVIEW SYMBOL" items={coins} setItems={setCoins}
            fields={[
              { key: "label", placeholder: "BTCUSDT", w: "1fr" },
              { key: "symbol", placeholder: "MEXC:BTCUSDT", w: "1.4fr", mono: true },
            ]} />
        </section>

        {/* Feeds */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>News sources (RSS)</h1>
            <button onClick={saveFeeds} disabled={savingFeeds}
              style={{ padding: "8px 20px", borderRadius: 9, border: "none", background: "var(--accent)", color: "#000", fontSize: 13, fontWeight: 700, cursor: savingFeeds ? "default" : "pointer", opacity: savingFeeds ? 0.7 : 1 }}>
              {savingFeeds ? "Saving..." : "Save"}
            </button>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>Saving fetches the new feeds immediately. Some sites (Cloudflare) block server-side requests.</p>
          <ListEditor title="NAME · RSS URL" items={feeds} setItems={setFeeds}
            fields={[
              { key: "name", placeholder: "CoinDesk", w: "1fr" },
              { key: "url", placeholder: "https://…/rss", w: "2fr", mono: true },
            ]} />
        </section>
      </main>
    </div>
  );
}

export default function AdminApp() {
  const [token, setToken] = useState(() => getToken());
  const logout = () => { localStorage.removeItem("cn_admin_token"); setToken(null); };
  if (!token) return <Login onLogin={setToken} />;
  return <Dashboard token={token} onLogout={logout} />;
}
