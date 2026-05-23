import logging
from telegram.ext import ContextTypes
from database import get_all_watches, get_user, update_watch, get_all_users, get_watches
from services import github_api as gh

logger = logging.getLogger(__name__)


async def check_watched_repos(context: ContextTypes.DEFAULT_TYPE):
    """Poll all watched repos for new commits and issues."""
    watches = get_all_watches()

    for watch in watches:
        tid = watch["telegram_id"]
        full_name = watch["repo_full_name"]
        user = get_user(tid)
        if not user:
            continue

        token = user["github_token"]
        try:
            owner, repo = full_name.split("/", 1)
        except ValueError:
            continue

        try:
            # New commits
            commits = gh.get_latest_commits(token, owner, repo, per_page=1)
            if commits:
                sha = commits[0]["sha"]
                if watch["last_commit_sha"] and sha != watch["last_commit_sha"]:
                    msg = commits[0]["commit"]["message"].splitlines()[0][:60]
                    author = commits[0]["commit"]["author"]["name"]
                    await context.bot.send_message(
                        chat_id=tid,
                        text=(
                            f"🔔 *New commit in `{full_name}`*\n\n"
                            f"`{sha[:7]}` — {msg}\n👤 {author}"
                        ),
                        parse_mode="Markdown",
                    )
                update_watch(tid, full_name, last_commit_sha=sha)

            # New issues
            issues = gh.get_issues(token, owner, repo)
            if issues:
                num = issues[0]["number"]
                if watch["last_issue_number"] and num > watch["last_issue_number"]:
                    await context.bot.send_message(
                        chat_id=tid,
                        text=(
                            f"🐛 *New issue in `{full_name}`*\n\n"
                            f"#{num} — {issues[0]['title']}\n"
                            f"🔗 {issues[0]['html_url']}"
                        ),
                        parse_mode="Markdown",
                    )
                update_watch(tid, full_name, last_issue_number=num)

            # New PRs
            prs = gh.get_pull_requests(token, owner, repo)
            if prs:
                pr_num = prs[0]["number"]
                if watch["last_pr_number"] and pr_num > watch["last_pr_number"]:
                    await context.bot.send_message(
                        chat_id=tid,
                        text=(
                            f"🔀 *New PR in `{full_name}`*\n\n"
                            f"#{pr_num} — {prs[0]['title']}\n"
                            f"🔗 {prs[0]['html_url']}"
                        ),
                        parse_mode="Markdown",
                    )
                update_watch(tid, full_name, last_pr_number=pr_num)

        except Exception as e:
            logger.error(f"Watch error [{full_name}] user {tid}: {e}")


async def send_daily_digest(context: ContextTypes.DEFAULT_TYPE):
    """Send daily activity summary to all users with watched repos."""
    users = get_all_users()

    for user in users:
        tid = user["telegram_id"]
        token = user["github_token"]
        username = user["github_username"] or "there"
        watches = get_watches(tid)

        if not watches:
            continue

        lines = [f"📅 *Daily Digest — {username}*\n"]

        for watch in watches[:6]:
            full_name = watch["repo_full_name"]
            try:
                owner, repo = full_name.split("/", 1)
                commits = gh.get_latest_commits(token, owner, repo, per_page=3)
                issues = gh.get_issues(token, owner, repo)
                prs = gh.get_pull_requests(token, owner, repo)
                lines.append(
                    f"\n📦 *{full_name}*\n"
                    f"  📝 {len(commits)} recent commits\n"
                    f"  🐛 {len(issues)} open issues\n"
                    f"  🔀 {len(prs)} open PRs"
                )
            except Exception:
                lines.append(f"\n📦 *{full_name}* — ⚠️ Could not fetch data")

        try:
            await context.bot.send_message(
                chat_id=tid,
                text="\n".join(lines),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Digest error for {tid}: {e}")
