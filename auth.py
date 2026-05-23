from functools import wraps
from database import get_user


def require_login(func):
    """Ensure user has connected their GitHub account via /login."""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text(
                "🔑 You need to connect your GitHub account first.\n\n"
                "Use `/login <your_github_pat>` to get started.\n"
                "Type `/login` for instructions.",
                parse_mode="Markdown"
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def get_user_ctx(telegram_id):
    """Return (token, github_username, active_repo, active_branch) for a user."""
    user = get_user(telegram_id)
    if not user:
        return None, None, None, "main"
    return (
        user["github_token"],
        user["github_username"],
        user["active_repo"],
        user["active_branch"] or "main",
    )
