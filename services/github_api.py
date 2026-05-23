import base64
import requests

BASE = "https://api.github.com"


def _h(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _get(token, path, params=None):
    r = requests.get(f"{BASE}{path}", headers=_h(token), params=params)
    r.raise_for_status()
    return r.json()


def _post(token, path, body):
    r = requests.post(f"{BASE}{path}", headers=_h(token), json=body)
    r.raise_for_status()
    return r.json()


def _patch(token, path, body):
    r = requests.patch(f"{BASE}{path}", headers=_h(token), json=body)
    r.raise_for_status()
    return r.json()


def _put(token, path, body=None):
    r = requests.put(f"{BASE}{path}", headers=_h(token), json=body or {})
    r.raise_for_status()
    return r.json()


# ── Auth ──────────────────────────────────────────────────────────────────────

def validate_token(token):
    r = requests.get(f"{BASE}/user", headers=_h(token))
    r.raise_for_status()
    return r.json()


# ── Repos ─────────────────────────────────────────────────────────────────────

def get_repos(token, per_page=15):
    return _get(token, "/user/repos", {"sort": "updated", "per_page": per_page})


def get_repo_info(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}")


def search_repos(token, query, per_page=8):
    return _get(token, "/search/repositories", {"q": query, "per_page": per_page})


# ── Branches ──────────────────────────────────────────────────────────────────

def get_branches(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/branches")


def create_branch(token, owner, repo, new_branch, from_branch="main"):
    ref = _get(token, f"/repos/{owner}/{repo}/git/ref/heads/{from_branch}")
    sha = ref["object"]["sha"]
    return _post(token, f"/repos/{owner}/{repo}/git/refs",
                 {"ref": f"refs/heads/{new_branch}", "sha": sha})


# ── Files ─────────────────────────────────────────────────────────────────────

def get_files(token, owner, repo, path="", branch="main"):
    return _get(token, f"/repos/{owner}/{repo}/contents/{path}", {"ref": branch})


def get_readme(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/readme")


def create_file(token, owner, repo, path, content, message, branch="main"):
    encoded = base64.b64encode(content.encode()).decode()
    return _put(token, f"/repos/{owner}/{repo}/contents/{path}", {
        "message": message,
        "content": encoded,
        "branch": branch,
    })


def search_code(token, query, owner=None, repo=None):
    q = query
    if owner and repo:
        q += f" repo:{owner}/{repo}"
    return _get(token, "/search/code", {"q": q, "per_page": 10})


# ── Issues ────────────────────────────────────────────────────────────────────

def get_issues(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/issues",
                {"state": "open", "per_page": 10})


def create_issue(token, owner, repo, title, body=""):
    return _post(token, f"/repos/{owner}/{repo}/issues",
                 {"title": title, "body": body})


def close_issue(token, owner, repo, number):
    return _patch(token, f"/repos/{owner}/{repo}/issues/{number}",
                  {"state": "closed"})


# ── Pull Requests ─────────────────────────────────────────────────────────────

def get_pull_requests(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/pulls",
                {"state": "open", "per_page": 10})


def merge_pr(token, owner, repo, pr_number, message="Merged via GIT KING Bot"):
    r = requests.put(
        f"{BASE}/repos/{owner}/{repo}/pulls/{pr_number}/merge",
        headers=_h(token),
        json={"commit_message": message},
    )
    r.raise_for_status()
    return r.json()


# ── Collaborators ─────────────────────────────────────────────────────────────

def add_collaborator(token, owner, repo, username, permission="push"):
    r = requests.put(
        f"{BASE}/repos/{owner}/{repo}/collaborators/{username}",
        headers=_h(token),
        json={"permission": permission},
    )
    r.raise_for_status()
    return r.status_code


# ── Commits ───────────────────────────────────────────────────────────────────

def get_latest_commits(token, owner, repo, branch="main", per_page=5):
    return _get(token, f"/repos/{owner}/{repo}/commits",
                {"sha": branch, "per_page": per_page})


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_contributors(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/contributors", {"per_page": 10})


def get_languages(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/languages")


def get_traffic_views(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/traffic/views")


def get_traffic_clones(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/traffic/clones")


def get_commit_activity(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/stats/commit_activity")


# ── Workflows (GitHub Actions) ────────────────────────────────────────────────

def get_workflows(token, owner, repo):
    return _get(token, f"/repos/{owner}/{repo}/actions/workflows")


def get_workflow_runs(token, owner, repo, workflow_id, per_page=5):
    return _get(token, f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
                {"per_page": per_page})


def get_latest_run(token, owner, repo, workflow_id):
    runs = get_workflow_runs(token, owner, repo, workflow_id, per_page=1)
    runs_list = runs.get("workflow_runs", [])
    return runs_list[0] if runs_list else None


def trigger_workflow(token, owner, repo, workflow_id, ref="main"):
    r = requests.post(
        f"{BASE}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
        headers=_h(token),
        json={"ref": ref},
    )
    r.raise_for_status()
    return r.status_code


def get_run_logs_url(token, owner, repo, run_id):
    r = requests.get(
        f"{BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/logs",
        headers=_h(token),
        allow_redirects=False,
    )
    return r.headers.get("Location", "Logs URL not available")


# ── Git Trees API — batch file push ──────────────────────────────────────────

def push_files_batch(token, owner, repo, branch, files_dict, message="Upload via GIT KING Bot"):
    """
    Push multiple files in a single commit using the Git Trees API.

    files_dict: { "path/to/file.py": {"content": "...", "encoding": "utf-8"|"base64"} }
    Returns the commit URL on GitHub.
    """
    # 1. Get latest commit SHA on branch
    ref = _get(token, f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
    latest_sha = ref["object"]["sha"]

    # 2. Get base tree SHA
    commit_data = _get(token, f"/repos/{owner}/{repo}/git/commits/{latest_sha}")
    base_tree_sha = commit_data["tree"]["sha"]

    # 3. Create a blob for each file
    tree_items = []
    for path, file_info in files_dict.items():
        blob = _post(token, f"/repos/{owner}/{repo}/git/blobs", {
            "content": file_info["content"],
            "encoding": file_info["encoding"],
        })
        tree_items.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })

    # 4. Create new tree
    new_tree = _post(token, f"/repos/{owner}/{repo}/git/trees", {
        "base_tree": base_tree_sha,
        "tree": tree_items,
    })

    # 5. Create new commit
    new_commit = _post(token, f"/repos/{owner}/{repo}/git/commits", {
        "message": message,
        "tree": new_tree["sha"],
        "parents": [latest_sha],
    })

    # 6. Update branch ref
    _patch(token, f"/repos/{owner}/{repo}/git/refs/heads/{branch}", {
        "sha": new_commit["sha"],
        "force": False,
    })

    return f"https://github.com/{owner}/{repo}/commit/{new_commit['sha']}"
