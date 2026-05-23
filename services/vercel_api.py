import requests
from config import VERCEL_TOKEN, VERCEL_DEPLOY_HOOK, VERCEL_PROJECT_ID

BASE = "https://api.vercel.com"
HEADERS = {"Authorization": f"Bearer {VERCEL_TOKEN}"}


def trigger_deploy():
    if not VERCEL_DEPLOY_HOOK:
        raise ValueError("VERCEL_DEPLOY_HOOK not set in .env")
    r = requests.post(VERCEL_DEPLOY_HOOK)
    r.raise_for_status()
    return r.json()


def get_deployments(limit=5):
    if not VERCEL_PROJECT_ID:
        raise ValueError("VERCEL_PROJECT_ID not set in .env")
    r = requests.get(f"{BASE}/v6/deployments",
                     headers=HEADERS,
                     params={"projectId": VERCEL_PROJECT_ID, "limit": limit})
    r.raise_for_status()
    return r.json().get("deployments", [])


def get_latest():
    deploys = get_deployments(limit=1)
    return deploys[0] if deploys else None
