import logging
from datetime import time as dt_time
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import TELEGRAM_TOKEN, DIGEST_HOUR, DIGEST_MINUTE, POLL_INTERVAL
from database import init_db
from scheduler import check_watched_repos, send_daily_digest

from handlers.general import start, help_command
from handlers.auth_handlers import cmd_login, cmd_logout, cmd_me
from handlers.github import (
    cmd_repos, cmd_repo, cmd_repoinfo, cmd_search,
    cmd_branches, cmd_branch,
    cmd_files, cmd_readme, cmd_createfile, cmd_findfile,
    cmd_issues, cmd_newissue, cmd_closeissue,
    cmd_prs, cmd_merge, cmd_invite,
)
from handlers.stats import cmd_stats, cmd_traffic
from handlers.workflow import cmd_workflows, cmd_runworkflow, cmd_wlogs
from handlers.deploy import cmd_deploy, cmd_deploystatus
from handlers.watch import cmd_watch, cmd_unwatch, cmd_watching
from handlers.upload import handle_zip_upload

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    init_db()
    logger.info("Database initialized.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # ── General ───────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # ── Auth ──────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("login", cmd_login))
    app.add_handler(CommandHandler("logout", cmd_logout))
    app.add_handler(CommandHandler("me", cmd_me))

    # ── Repos ─────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("repos", cmd_repos))
    app.add_handler(CommandHandler("repo", cmd_repo))
    app.add_handler(CommandHandler("repoinfo", cmd_repoinfo))
    app.add_handler(CommandHandler("search", cmd_search))

    # ── Branches ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("branches", cmd_branches))
    app.add_handler(CommandHandler("branch", cmd_branch))

    # ── Files ─────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("files", cmd_files))
    app.add_handler(CommandHandler("readme", cmd_readme))
    app.add_handler(CommandHandler("createfile", cmd_createfile))
    app.add_handler(CommandHandler("findfile", cmd_findfile))

    # ── Issues ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("issues", cmd_issues))
    app.add_handler(CommandHandler("newissue", cmd_newissue))
    app.add_handler(CommandHandler("closeissue", cmd_closeissue))

    # ── Pull Requests ─────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("prs", cmd_prs))
    app.add_handler(CommandHandler("merge", cmd_merge))

    # ── Collaboration ─────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("invite", cmd_invite))

    # ── Stats ─────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("traffic", cmd_traffic))

    # ── Workflows ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("workflows", cmd_workflows))
    app.add_handler(CommandHandler("runworkflow", cmd_runworkflow))
    app.add_handler(CommandHandler("wlogs", cmd_wlogs))

    # ── Deploy ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("deploy", cmd_deploy))
    app.add_handler(CommandHandler("deploystatus", cmd_deploystatus))

    # ── Watch / Notifications ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("watch", cmd_watch))
    app.add_handler(CommandHandler("unwatch", cmd_unwatch))
    app.add_handler(CommandHandler("watching", cmd_watching))

    # ── Zip Upload ────────────────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.Document.FileExtension("zip"), handle_zip_upload))

    # ── Scheduler ────────────────────────────────────────────────────────────
    job_queue = app.job_queue

    # Poll for repo activity every POLL_INTERVAL seconds
    job_queue.run_repeating(check_watched_repos, interval=POLL_INTERVAL, first=60)

    # Daily digest at configured time (UTC)
    job_queue.run_daily(
        send_daily_digest,
        time=dt_time(hour=DIGEST_HOUR, minute=DIGEST_MINUTE),
    )

    logger.info("👑 GIT KING Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
