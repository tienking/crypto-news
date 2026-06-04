from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
# Minutes between RSS refresh runs (in-app APScheduler).
REFRESH_MINUTES = int(os.getenv("REFRESH_MINUTES", "15"))
