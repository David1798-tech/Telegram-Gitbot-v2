import requests
from config import NETLIFY_TOKEN, NETLIFY_DEPLOY_HOOK, NETLIFY_SITE_ID

BASE = "https://api.netlify.com/api/v1"


def _headers():
    return {"Authorization": f"Bearer {NETLIFY_TOKEN}"}


def trigger_deploy():
    if not NETLIFY_DEPLOY_HOOK:
        raise ValueError("NETLIFY_DEPLOY_HOOK not set in .env")
    r = requests.post(NETLIFY_DEPLOY_HOOK)
    r.raise_for_status()
    return r.json()


def get_deployments(limit=5):
    if not NETLIFY_SITE_ID:
        raise ValueError("NETLIFY_SITE_ID not set in .env")
    r = requests.get(f"{BASE}/sites/{NETLIFY_SITE_ID}/deploys",
                     headers=_headers(), params={"per_page": limit})
    r.raise_for_status()
    return r.json()


def get_latest():
    deploys = get_deployments(limit=1)
    return deploys[0] if deploys else None


def get_site_info():
    if not NETLIFY_SITE_ID:
        raise ValueError("NETLIFY_SITE_ID not set in .env")
    r = requests.get(f"{BASE}/sites/{NETLIFY_SITE_ID}", headers=_headers())
    r.raise_for_status()
    return r.json()
