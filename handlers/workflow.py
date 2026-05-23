from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login, get_user_ctx
from services import github_api as gh


@require_login
async def cmd_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        data = gh.get_workflows(token, username, repo)
        workflows = data.get("workflows", [])
        if not workflows:
            await update.message.reply_text(f"No workflows found in `{repo}`", parse_mode="Markdown")
            return
        lines = [f"⚙️ *Workflows — {repo}*\n"]
        for w in workflows:
            state = "✅" if w["state"] == "active" else "⏸"
            lines.append(f"{state} `{w['id']}` — {w['name']}")
        lines.append("\n`/runworkflow <id>` to trigger one.")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


@require_login
async def cmd_runworkflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/runworkflow <workflow_id>`", parse_mode="Markdown")
        return
    wf_id = context.args[0]
    try:
        status = gh.trigger_workflow(token, username, repo, wf_id, ref=branch)
        if status == 204:
            await update.message.reply_text(
                f"✅ Workflow `{wf_id}` triggered on `{branch}`", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"Response: {status}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


@require_login
async def cmd_wlogs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/wlogs <workflow_id>`", parse_mode="Markdown")
        return
    wf_id = context.args[0]
    try:
        run = gh.get_latest_run(token, username, repo, wf_id)
        if not run:
            await update.message.reply_text("No runs found for this workflow.")
            return
        status_map = {
            "completed": "✅", "in_progress": "🔄",
            "queued": "⏳", "failure": "❌"
        }
        conclusion = run.get("conclusion") or run.get("status", "unknown")
        emoji = status_map.get(conclusion, "❓")
        logs_url = gh.get_run_logs_url(token, username, repo, run["id"])
        await update.message.reply_text(
            f"{emoji} *Latest Run — Workflow {wf_id}*\n\n"
            f"Status: `{run.get('status')}`\n"
            f"Conclusion: `{run.get('conclusion') or 'N/A'}`\n"
            f"Branch: `{run.get('head_branch')}`\n"
            f"Started: {run.get('created_at', '')[:19]}\n\n"
            f"📋 Logs: {logs_url}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
