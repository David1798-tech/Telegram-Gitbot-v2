from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login, get_user_ctx
from services import github_api as gh


@require_login
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        info = gh.get_repo_info(token, username, repo)
        languages = gh.get_languages(token, username, repo)
        contributors = gh.get_contributors(token, username, repo)

        total_bytes = sum(languages.values()) or 1
        lang_lines = "\n".join(
            f"  `{lang}` — {round(b / total_bytes * 100, 1)}%"
            for lang, b in sorted(languages.items(), key=lambda x: -x[1])[:6]
        ) or "  N/A"

        top_contributors = "\n".join(
            f"  `{c['login']}` — {c['contributions']} commits"
            for c in contributors[:5]
        ) or "  N/A"

        await update.message.reply_text(
            f"📊 *Stats — {repo}*\n\n"
            f"⭐ Stars: {info['stargazers_count']}\n"
            f"🍴 Forks: {info['forks_count']}\n"
            f"👁 Watchers: {info['watchers_count']}\n"
            f"🐛 Open issues: {info['open_issues_count']}\n"
            f"📏 Size: {info['size']} KB\n\n"
            f"*Languages:*\n{lang_lines}\n\n"
            f"*Top Contributors:*\n{top_contributors}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


@require_login
async def cmd_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        views = gh.get_traffic_views(token, username, repo)
        clones = gh.get_traffic_clones(token, username, repo)
        await update.message.reply_text(
            f"📈 *Traffic — {repo}* (last 14 days)\n\n"
            f"👁 Views: {views.get('count', 0)} total, {views.get('uniques', 0)} unique\n"
            f"📥 Clones: {clones.get('count', 0)} total, {clones.get('uniques', 0)} unique",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ {e}\n\n_(Traffic data is only available to repo owners)_",
            parse_mode="Markdown",
        )
