from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login
from services import vercel_api, render_api, netlify_api, flyio_api


PLATFORMS = ["vercel", "render", "netlify", "fly"]


def _usage_msg():
    opts = "|".join(PLATFORMS)
    return f"Usage: `/deploy {opts}`"


@require_login
async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(_usage_msg(), parse_mode="Markdown")
        return

    platform = context.args[0].lower()

    if platform not in PLATFORMS:
        await update.message.reply_text(
            f"❌ Unknown platform. {_usage_msg()}", parse_mode="Markdown"
        )
        return

    await update.message.reply_text(f"🚀 Triggering {platform.capitalize()} deploy...")

    try:
        if platform == "vercel":
            result = vercel_api.trigger_deploy()
            job = result.get("job", {}).get("id", "triggered")
            await update.message.reply_text(
                f"✅ Vercel deploy triggered! Job: `{job}`\n"
                f"Use `/deploystatus vercel` to check.",
                parse_mode="Markdown",
            )

        elif platform == "render":
            render_api.trigger_deploy()
            await update.message.reply_text(
                "✅ Render deploy triggered!\n"
                "Use `/deploystatus render` to check.",
                parse_mode="Markdown",
            )

        elif platform == "netlify":
            netlify_api.trigger_deploy()
            await update.message.reply_text(
                "✅ Netlify deploy triggered!\n"
                "Use `/deploystatus netlify` to check.",
                parse_mode="Markdown",
            )

        elif platform == "fly":
            await update.message.reply_text(
                "⚠️ Fly.io deploys require `flyctl deploy` from your terminal.\n\n"
                "Use `/deploystatus fly` to check the current status.",
                parse_mode="Markdown",
            )

    except ValueError as e:
        await update.message.reply_text(
            f"⚠️ {e}\n\nAdd this to your `.env` file.", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Deploy failed: {e}")


@require_login
async def cmd_deploystatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"Usage: `/deploystatus {'|'.join(PLATFORMS)}`", parse_mode="Markdown"
        )
        return

    platform = context.args[0].lower()

    try:
        if platform == "vercel":
            d = vercel_api.get_latest()
            if not d:
                await update.message.reply_text("No Vercel deployments found.")
                return
            state = d.get("state", "unknown").upper()
            emoji = {"READY": "✅", "ERROR": "❌", "BUILDING": "🔄", "QUEUED": "⏳"}.get(state, "❓")
            await update.message.reply_text(
                f"{emoji} *Vercel — Latest Deploy*\n\n"
                f"Project: `{d.get('name', 'N/A')}`\n"
                f"Status: `{state}`\n"
                f"URL: https://{d.get('url', 'N/A')}",
                parse_mode="Markdown",
            )

        elif platform == "render":
            d = render_api.get_latest()
            if not d:
                await update.message.reply_text("No Render deployments found.")
                return
            status = d.get("status", "unknown").upper()
            emoji = {"LIVE": "✅", "BUILD_FAILED": "❌", "INPROGRESS": "🔄"}.get(status, "❓")
            await update.message.reply_text(
                f"{emoji} *Render — Latest Deploy*\n\n"
                f"ID: `{d.get('id', 'N/A')}`\n"
                f"Status: `{status}`\n"
                f"Created: {d.get('createdAt', 'N/A')[:19]}",
                parse_mode="Markdown",
            )

        elif platform == "netlify":
            d = netlify_api.get_latest()
            if not d:
                await update.message.reply_text("No Netlify deployments found.")
                return
            state = d.get("state", "unknown")
            emoji = {"ready": "✅", "error": "❌", "building": "🔄", "enqueued": "⏳"}.get(state, "❓")
            await update.message.reply_text(
                f"{emoji} *Netlify — Latest Deploy*\n\n"
                f"ID: `{d.get('id', 'N/A')}`\n"
                f"State: `{state}`\n"
                f"Branch: `{d.get('branch', 'N/A')}`\n"
                f"URL: {d.get('deploy_ssl_url') or d.get('url', 'N/A')}",
                parse_mode="Markdown",
            )

        elif platform == "fly":
            info = flyio_api.get_app_status()
            release = info.get("currentRelease") or {}
            status = info.get("status", "unknown")
            emoji = {"running": "✅", "deployed": "✅", "suspended": "⏸"}.get(status, "❓")
            await update.message.reply_text(
                f"{emoji} *Fly.io — {info.get('name', 'N/A')}*\n\n"
                f"Status: `{status}`\n"
                f"Release: v{release.get('version', 'N/A')} — `{release.get('status', 'N/A')}`\n"
                f"Deployed at: {release.get('createdAt', 'N/A')[:19]}",
                parse_mode="Markdown",
            )

        else:
            await update.message.reply_text(
                f"❌ Unknown platform. Use: {' | '.join(PLATFORMS)}", parse_mode="Markdown"
            )

    except ValueError as e:
        await update.message.reply_text(
            f"⚠️ {e}\n\nAdd this to your `.env` file.", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
