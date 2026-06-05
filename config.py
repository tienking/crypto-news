from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
# Minutes between RSS refresh runs (in-app APScheduler).
REFRESH_MINUTES = int(os.getenv("REFRESH_MINUTES", "15"))

# Grok (xAI) — OpenAI-compatible chat API.
XAI_API_KEY = os.getenv("XAI_API_KEY")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3")
XAI_BASE_URL = "https://api.x.ai/v1/chat/completions"

# Admin auth.
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")  # used to seed admin on first run
