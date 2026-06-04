import { timeAgo } from "../lib/api";

export default function ArticleCard({ article, onOpen, featured }) {
  const { title, summary, image, source, published } = article;
  return (
    <article
      onClick={() => onOpen(article)}
      style={{
        background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 14,
        overflow: "hidden", cursor: "pointer", display: "flex", flexDirection: "column",
        transition: "border-color .15s, transform .15s",
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--border-hover)"; e.currentTarget.style.transform = "translateY(-2px)"; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.transform = ""; }}
    >
      {image && (
        <div style={{ width: "100%", aspectRatio: featured ? "16/8" : "16/9", overflow: "hidden", background: "var(--bg-surface)" }}>
          <img src={image} alt="" loading="lazy" referrerPolicy="no-referrer"
            onError={e => { e.currentTarget.parentElement.style.display = "none"; }}
            style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      )}
      <div style={{ padding: featured ? "18px 20px" : "14px 16px", display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontFamily: "var(--font-mono)" }}>
          <span style={{ color: "var(--accent)", fontWeight: 600 }}>{source}</span>
          <span style={{ color: "var(--text-dim)" }}>·</span>
          <span style={{ color: "var(--text-muted)" }}>{timeAgo(published)}</span>
        </div>
        <h3 style={{ fontSize: featured ? 22 : 15, fontWeight: 700, lineHeight: 1.3, color: "var(--text)" }}>{title}</h3>
        {summary && (
          <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, display: "-webkit-box", WebkitLineClamp: featured ? 3 : 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {summary}
          </p>
        )}
      </div>
    </article>
  );
}
