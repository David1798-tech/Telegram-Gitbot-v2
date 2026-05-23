import requests
from config import RENDER_API_KEY, RENDER_DEPLOY_HOOK, RENDER_SERVICE_ID

BASE = "https://api.render.com/v1"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}


def trigger_deploy():
    if not RENDER_DEPLOY_HOOK:
        raise ValueError("RENDER_DEPLOY_HOOK not set in .env")
    r = requests.post(RENDER_DEPLOY_HOOK)
    r.raise_for_status()
    return r.json()


def get_deployments(limit=5):
    if not RENDER_SERVICE_ID:
        raise ValueError("RENDER_SERVICE_ID not set in .env")
    r = requests.get(f"{BASE}/services/{RENDER_SERVICE_ID}/deploys",
                     headers=HEADERS, params={"limit": limit})
    r.raise_for_status()
    return r.json()


def get_latest():
    deploys = get_deployments(limit=1)
    if deploys and isinstance(deploys, list):
        return deploys[0].get("deploy")
    return None
