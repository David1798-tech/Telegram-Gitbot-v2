from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login
from database import save_user, delete_user
from services import github_api as gh


async def cmd_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔑 *Connect your GitHub account*\n\n"
            "Usage: `/login <your_github_pat>`\n\n"
            "*How to get a PAT:*\n"
            "1. github.com → Settings\n"
            "2. Developer Settings → Personal Access Tokens → Tokens (classic)\n"
            "3. Generate new token\n"
            "4. Select scopes: `repo`, `workflow`, `read:user`\n\n"
            "⚠️ Only send your token in a private chat with this bot.",
            parse_mode="Markdown",
        )
        return

    token = context.args[0]

    # Try to delete the message immediately for security
    try:
        await update.message.delete()
    except Exception:
        pass

    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔄 Validating token...",
    )

    try:
        info = gh.validate_token(token)
        username = info["login"]
        save_user(update.effective_user.id, token, username)
        await msg.edit_text(
            f"✅ *Logged in as `{username}`*\n\n"
            f"Public repos: {info.get('public_repos', 0)}\n"
            f"Your token is saved. Use `/repos` to get started.\n\n"
            f"⚠️ Your login message was deleted for security.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(f"❌ Login failed: {e}\n\nCheck that your PAT is valid.")


@require_login
async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delete_user(update.effective_user.id)
    await update.message.reply_text(
        "✅ Logged out. Your GitHub token and watched repos have been deleted."
    )


@require_login
async def cmd_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from auth import get_user_ctx
    token, username, _, _ = get_user_ctx(update.effective_user.id)
    try:
        info = gh.validate_token(token)
        await update.message.reply_text(
            f"👤 *{info.get('name') or info['login']}*\n\n"
            f"Username: `{info['login']}`\n"
            f"Public repos: {info.get('public_repos', 0)}\n"
            f"Followers: {info.get('followers', 0)} | Following: {info.get('following', 0)}\n"
            f"Bio: {info.get('bio') or 'N/A'}\n"
            f"🔗 {info['html_url']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
