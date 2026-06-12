from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
# Minutes between RSS refresh runs (in-app APScheduler).
REFRESH_MINUTES = int(os.getenv("REFRESH_MINUTES", "15"))
# Auto-delete articles older than this many days (MongoDB TTL index).
ARTICLE_TTL_DAYS = int(os.getenv("ARTICLE_TTL_DAYS", "30"))

# Chatbot providers. Active provider + per-provider model are stored in MongoDB
# (settings type="ai"); the env vars below are API keys + seed defaults.
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3")          # seed default

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # seed default

AI_PROVIDER = os.getenv("AI_PROVIDER", "grok")          # seed default: grok | gemini

# Admin auth.
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")  # used to seed admin on first run
