import sqlite3

DB_PATH = "gitbot.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id  INTEGER PRIMARY KEY,
            github_token TEXT NOT NULL,
            github_username TEXT,
            active_repo  TEXT,
            active_branch TEXT DEFAULT 'main',
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS watched_repos (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id        INTEGER NOT NULL,
            repo_full_name     TEXT NOT NULL,
            last_commit_sha    TEXT,
            last_issue_number  INTEGER,
            last_pr_number     INTEGER,
            UNIQUE(telegram_id, repo_full_name)
        )
    """)

    conn.commit()
    conn.close()


# ── Users ─────────────────────────────────────────────────────────────────────

def save_user(telegram_id, github_token, github_username):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO users (telegram_id, github_token, github_username)
        VALUES (?, ?, ?)
    """, (telegram_id, github_token, github_username))
    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    conn.close()
    return user


def delete_user(telegram_id):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
    conn.execute("DELETE FROM watched_repos WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


def update_session(telegram_id, active_repo=None, active_branch=None):
    conn = get_conn()
    if active_repo is not None:
        conn.execute(
            "UPDATE users SET active_repo = ?, active_branch = 'main' WHERE telegram_id = ?",
            (active_repo, telegram_id)
        )
    if active_branch is not None:
        conn.execute(
            "UPDATE users SET active_branch = ? WHERE telegram_id = ?",
            (active_branch, telegram_id)
        )
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_conn()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users


# ── Watched Repos ─────────────────────────────────────────────────────────────

def add_watch(telegram_id, repo_full_name, last_commit_sha=None,
              last_issue_number=None, last_pr_number=None):
    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO watched_repos
        (telegram_id, repo_full_name, last_commit_sha, last_issue_number, last_pr_number)
        VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, repo_full_name, last_commit_sha, last_issue_number, last_pr_number))
    conn.commit()
    conn.close()


def remove_watch(telegram_id, repo_full_name):
    conn = get_conn()
    conn.execute(
        "DELETE FROM watched_repos WHERE telegram_id = ? AND repo_full_name = ?",
        (telegram_id, repo_full_name)
    )
    conn.commit()
    conn.close()


def get_watches(telegram_id):
    conn = get_conn()
    watches = conn.execute(
        "SELECT * FROM watched_repos WHERE telegram_id = ?", (telegram_id,)
    ).fetchall()
    conn.close()
    return watches


def get_all_watches():
    conn = get_conn()
    watches = conn.execute("SELECT * FROM watched_repos").fetchall()
    conn.close()
    return watches


def update_watch(telegram_id, repo_full_name, last_commit_sha=None,
                 last_issue_number=None, last_pr_number=None):
    conn = get_conn()
    updates, values = [], []
    if last_commit_sha is not None:
        updates.append("last_commit_sha = ?")
        values.append(last_commit_sha)
    if last_issue_number is not None:
        updates.append("last_issue_number = ?")
        values.append(last_issue_number)
    if last_pr_number is not None:
        updates.append("last_pr_number = ?")
        values.append(last_pr_number)
    if updates:
        values.extend([telegram_id, repo_full_name])
        conn.execute(
            f"UPDATE watched_repos SET {', '.join(updates)} "
            f"WHERE telegram_id = ? AND repo_full_name = ?",
            values
        )
        conn.commit()
    conn.close()
