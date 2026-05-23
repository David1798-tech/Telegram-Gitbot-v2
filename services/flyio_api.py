import requests
from config import FLY_API_TOKEN, FLY_APP_NAME

GRAPHQL = "https://api.fly.io/graphql"


def _headers():
    return {"Authorization": f"Bearer {FLY_API_TOKEN}"}


def get_app_status():
    if not FLY_APP_NAME:
        raise ValueError("FLY_APP_NAME not set in .env")
    query = """
    query($appName: String!) {
        app(name: $appName) {
            name
            status
            deployed
            currentRelease {
                version
                status
                reason
                createdAt
            }
        }
    }
    """
    r = requests.post(GRAPHQL, headers=_headers(),
                      json={"query": query, "variables": {"appName": FLY_APP_NAME}})
    r.raise_for_status()
    return r.json().get("data", {}).get("app", {})


def get_releases(limit=5):
    if not FLY_APP_NAME:
        raise ValueError("FLY_APP_NAME not set in .env")
    query = """
    query($appName: String!, $limit: Int) {
        app(name: $appName) {
            releases(first: $limit) {
                nodes { version status reason createdAt }
            }
        }
    }
    """
    r = requests.post(GRAPHQL, headers=_headers(),
                      json={"query": query,
                            "variables": {"appName": FLY_APP_NAME, "limit": limit}})
    r.raise_for_status()
    data = r.json().get("data", {}).get("app", {})
    return data.get("releases", {}).get("nodes", [])
