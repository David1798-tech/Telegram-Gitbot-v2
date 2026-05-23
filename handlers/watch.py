from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login, get_user_ctx
from database import add_watch, remove_watch, get_watches
from services import github_api as gh


@require_login
async def cmd_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    full_name = f"{username}/{repo}"
    try:
        commits = gh.get_latest_commits(token, username, repo, branch, per_page=1)
        issues = gh.get_issues(token, username, repo)
        prs = gh.get_pull_requests(token, username, repo)

        last_sha = commits[0]["sha"] if commits else None
        last_issue = issues[0]["number"] if issues else None
        last_pr = prs[0]["number"] if prs else None

        add_watch(update.effective_user.id, full_name, last_sha, last_issue, last_pr)
        await update.message.reply_text(
            f"🔔 Now watching `{full_name}`\n\n"
            f"You'll get alerts on new commits, issues, and PRs.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


@require_login
async def cmd_unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    full_name = f"{username}/{repo}"
    remove_watch(update.effective_user.id, full_name)
    await update.message.reply_text(
        f"🔕 Stopped watching `{full_name}`", parse_mode="Markdown"
    )


@require_login
async def cmd_watching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watches = get_watches(update.effective_user.id)
    if not watches:
        await update.message.reply_text(
            "You're not watching any repos.\nUse `/watch` to start.", parse_mode="Markdown"
        )
        return
    lines = ["👁 *Watched Repos*\n"]
    for w in watches:
        lines.append(f"• `{w['repo_full_name']}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
