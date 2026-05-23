import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Deploy platform credentials (per-bot owner, not per-user)
VERCEL_TOKEN      = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")
VERCEL_DEPLOY_HOOK = os.getenv("VERCEL_DEPLOY_HOOK")

RENDER_API_KEY    = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
RENDER_DEPLOY_HOOK = os.getenv("RENDER_DEPLOY_HOOK")

NETLIFY_TOKEN     = os.getenv("NETLIFY_TOKEN")
NETLIFY_SITE_ID   = os.getenv("NETLIFY_SITE_ID")
NETLIFY_DEPLOY_HOOK = os.getenv("NETLIFY_DEPLOY_HOOK")

FLY_API_TOKEN     = os.getenv("FLY_API_TOKEN")
FLY_APP_NAME      = os.getenv("FLY_APP_NAME")

# Daily digest time (24h format)
DIGEST_HOUR   = int(os.getenv("DIGEST_HOUR", "8"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))

# Notification polling interval in seconds
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))  # 5 min default
