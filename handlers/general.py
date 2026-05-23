from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 *GIT KING Bot*\n\n"
        "Manage your GitHub repos and deployments from Telegram.\n\n"
        "Get started by connecting your GitHub account:\n"
        "`/login <your_github_pat>`\n\n"
        "Type `/help` to see all commands.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👑 *GIT KING — Command Reference*\n\n"

        "*🔑 Account*\n"
        "`/login <token>` — Connect GitHub account\n"
        "`/logout` — Disconnect & delete your data\n"
        "`/me` — Your GitHub profile\n\n"

        "*🗂 Repos*\n"
        "`/repos` — List your repos\n"
        "`/repo <name>` — Set active repo\n"
        "`/repoinfo` — Info + recent commits\n"
        "`/search <query>` — Search GitHub repos\n\n"

        "*🌿 Branches*\n"
        "`/branches` — List branches\n"
        "`/branch <name>` — Switch or create branch\n\n"

        "*📁 Files*\n"
        "`/files [path]` — Browse files\n"
        "`/readme` — View README\n"
        "`/createfile <path> | <content> | <msg>` — Create a file\n"
        "`/findfile <filename>` — Search file in repo\n\n"

        "*🐛 Issues*\n"
        "`/issues` — Open issues\n"
        "`/newissue <title> | <body>` — Create issue\n"
        "`/closeissue <number>` — Close an issue\n\n"

        "*🔀 Pull Requests*\n"
        "`/prs` — Open PRs\n"
        "`/merge <number>` — Merge a PR\n\n"

        "*🤝 Collaboration*\n"
        "`/invite <username>` — Add collaborator\n\n"

        "*📊 Stats*\n"
        "`/stats` — Repo stats & languages\n"
        "`/traffic` — Views & clones (owners only)\n\n"

        "*⚙️ Workflows*\n"
        "`/workflows` — List GitHub Actions\n"
        "`/runworkflow <id>` — Trigger a workflow\n"
        "`/wlogs <workflow_id>` — Latest run logs URL\n\n"

        "*🚀 Deploy*\n"
        "`/deploy vercel|render|netlify|fly` — Trigger deploy\n"
        "`/deploystatus vercel|render|netlify|fly` — Deploy status\n\n"

        "*🔔 Notifications*\n"
        "`/watch` — Watch active repo\n"
        "`/unwatch` — Stop watching\n"
        "`/watching` — List watched repos\n"
        "_(Auto-alerts on new commits, issues, PRs)_\n"
        "_(Daily digest sent every morning)_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
