import { useState, useEffect, useCallback, useRef } from "react";
import { fetchArticles, fetchSources } from "./lib/api";
import ArticleCard from "./components/ArticleCard";
import Reader from "./components/Reader";
import ChatPopup from "./components/ChatPopup";
import MarketChart from "./components/MarketChart";

const LIMIT = 24;

export default function App() {
  const [articles, setArticles] = useState([]);
  const [sources, setSources] = useState([]);
  const [source, setSource] = useState("");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");      // debounced query actually sent
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reading, setReading] = useState(null);  // article id being read
  const searchTimer = useRef(null);

  useEffect(() => { fetchSources().then(setSources).catch(() => {}); }, []);

  // Debounce the search box.
  useEffect(() => {
    clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => { setSearch(q); setPage(1); }, 350);
    return () => clearTimeout(searchTimer.current);
  }, [q]);

  const load = useCallback(async (reset) => {
    setLoading(true);
    try {
      const data = await fetchArticles({ page: reset ? 1 : page, limit: LIMIT, source, q: search });
      setTotal(data.total);
      setArticles(prev => reset ? data.items : [...prev, ...data.items]);
    } catch { /* ignore */ }
    setLoading(false);
  }, [page, source, search]);

  // Reset list when filters change.
  useEffect(() => { setPage(1); load(true); /* eslint-disable-next-line */ }, [source, search]);
  // Append when page advances.
  useEffect(() => { if (page > 1) load(false); /* eslint-disable-next-line */ }, [page]);

  if (reading) return (
    <div style={{ minHeight: "100vh" }}>
      <Reader id={reading} onBack={() => setReading(null)} />
      <ChatPopup />
    </div>
  );

  const hasMore = articles.length < total;
  const [featured, ...rest] = articles;

  return (
    <div style={{ minHeight: "100vh" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-surface)", position: "sticky", top: 0, zIndex: 10 }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>
              Crypto<span style={{ color: "var(--accent)" }}>News</span>
            </h1>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="🔍 Search news..."
              style={{ fontSize: 13, padding: "9px 14px", borderRadius: 10, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", outline: "none", width: 240, fontFamily: "var(--font-display)" }} />
            <a href="/projects/crypto-news/admin"
              style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "none", border: "1px solid var(--border)", borderRadius: 9, padding: "8px 14px", whiteSpace: "nowrap" }}>
              Admin
            </a>
          </div>
        </div>

        {/* Source filter chips */}
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px 12px", display: "flex", gap: 8, overflowX: "auto" }}>
          <Chip active={!source} onClick={() => setSource("")}>All</Chip>
          {sources.map(s => <Chip key={s} active={source === s} onClick={() => setSource(s)}>{s}</Chip>)}
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 24px 60px" }}>
        <MarketChart />
        {loading && articles.length === 0 ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
            <div style={{ width: 26, height: 26, borderRadius: "50%", border: "2px solid var(--accent)", borderTopColor: "transparent", animation: "spin .8s linear infinite" }} />
          </div>
        ) : articles.length === 0 ? (
          <p style={{ textAlign: "center", color: "var(--text-muted)", padding: "80px 0" }}>No articles found.</p>
        ) : (
          <>
            {/* Featured (first article, full width) */}
            {!search && !source && featured && (
              <div style={{ marginBottom: 20 }}>
                <ArticleCard article={featured} onOpen={a => setReading(a.id)} featured />
              </div>
            )}

            {/* Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
              {(!search && !source ? rest : articles).map(a => (
                <ArticleCard key={a.id} article={a} onOpen={x => setReading(x.id)} />
              ))}
            </div>

            {hasMore && (
              <div style={{ textAlign: "center", marginTop: 32 }}>
                <button onClick={() => setPage(p => p + 1)} disabled={loading}
                  style={{ fontSize: 14, padding: "11px 28px", borderRadius: 10, border: "1px solid var(--border)", background: "var(--bg-card)", color: "var(--text)", cursor: loading ? "default" : "pointer", fontFamily: "var(--font-display)" }}>
                  {loading ? "Loading..." : "Load more"}
                </button>
              </div>
            )}
          </>
        )}
      </main>

      <ChatPopup />
    </div>
  );
}

function Chip({ active, onClick, children }) {
  return (
    <button onClick={onClick}
      style={{
        flexShrink: 0, fontSize: 12, padding: "6px 14px", borderRadius: 20, cursor: "pointer",
        fontFamily: "var(--font-display)", whiteSpace: "nowrap",
        border: `1px solid ${active ? "var(--accent-border)" : "var(--border)"}`,
        background: active ? "var(--accent-dim)" : "transparent",
        color: active ? "var(--accent)" : "var(--text-muted)",
      }}>
      {children}
    </button>
  );
}
