import { useState, useEffect } from "react";
import { fetchArticle, timeAgo } from "../lib/api";

export default function Reader({ id, onBack }) {
  const [article, setArticle] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
    fetchArticle(id).then(setArticle).catch(() => setError(true));
  }, [id]);

  if (error) return (
    <div style={{ maxWidth: 760, margin: "60px auto", textAlign: "center", color: "var(--text-muted)" }}>
      Article not found. <button onClick={onBack} style={linkBtn}>Back</button>
    </div>
  );

  if (!article) return (
    <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
      <div style={{ width: 26, height: 26, borderRadius: "50%", border: "2px solid var(--accent)", borderTopColor: "transparent", animation: "spin .8s linear infinite" }} />
    </div>
  );

  return (
    <article style={{ maxWidth: 760, margin: "0 auto", padding: "20px 24px 80px", animation: "fadeUp .3s ease both" }}>
      <button onClick={onBack} style={{ ...linkBtn, marginBottom: 24 }}>← Back to news</button>

      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, fontFamily: "var(--font-mono)", marginBottom: 12 }}>
        <span style={{ color: "var(--accent)", fontWeight: 600 }}>{article.source}</span>
        <span style={{ color: "var(--text-dim)" }}>·</span>
        <span style={{ color: "var(--text-muted)" }}>{timeAgo(article.published)}</span>
        {article.author && <><span style={{ color: "var(--text-dim)" }}>·</span><span style={{ color: "var(--text-muted)" }}>{article.author}</span></>}
      </div>

      <h1 style={{ fontSize: 30, fontWeight: 800, lineHeight: 1.25, marginBottom: 20 }}>{article.title}</h1>

      {article.image && (
        <img src={article.image} alt="" referrerPolicy="no-referrer"
          onError={e => { e.currentTarget.style.display = "none"; }}
          style={{ width: "100%", borderRadius: 14, marginBottom: 24, border: "1px solid var(--border)" }} />
      )}

      <div className="article-body"
        style={{ fontSize: 16, lineHeight: 1.8, color: "var(--text)" }}
        dangerouslySetInnerHTML={{ __html: article.content || `<p>${article.summary || ""}</p>` }} />

      <div style={{ marginTop: 32, paddingTop: 20, borderTop: "1px solid var(--border)" }}>
        <a href={article.link} target="_blank" rel="noreferrer"
          style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 14, padding: "10px 20px", borderRadius: 10, background: "var(--accent)", color: "#000", fontWeight: 600, textDecoration: "none" }}>
          Read original on {article.source} →
        </a>
      </div>

      <style>{`
        .article-body img { max-width: 100%; height: auto; border-radius: 10px; margin: 16px 0; }
        .article-body p { margin: 0 0 16px; }
        .article-body a { color: var(--accent); }
        .article-body h2, .article-body h3 { margin: 24px 0 12px; font-weight: 700; }
        .article-body ul, .article-body ol { margin: 0 0 16px; padding-left: 22px; }
        .article-body li { margin-bottom: 6px; }
        .article-body figure { margin: 16px 0; }
        .article-body iframe { max-width: 100%; }
      `}</style>
    </article>
  );
}

const linkBtn = {
  background: "none", border: "1px solid var(--border)", borderRadius: 8,
  padding: "6px 14px", fontSize: 13, color: "var(--text-muted)", cursor: "pointer",
  fontFamily: "var(--font-display)",
};
