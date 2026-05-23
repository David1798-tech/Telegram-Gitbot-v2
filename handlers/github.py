from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login, get_user_ctx
from database import update_session
from services import github_api as gh


def _ctx(uid):
    return get_user_ctx(uid)


# ── /repos ────────────────────────────────────────────────────────────────────

@require_login
async def cmd_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, _, _ = _ctx(update.effective_user.id)
    try:
        repos = gh.get_repos(token)
        lines = [f"📦 *{username}'s Repos*\n"]
        for r in repos:
            vis = "🔒" if r["private"] else "🌐"
            lines.append(f"{vis} `{r['name']}` ⭐{r['stargazers_count']}")
        lines.append("\n`/repo <name>` to set active repo.")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /repo <name> ──────────────────────────────────────────────────────────────

@require_login
async def cmd_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, active_repo, active_branch = _ctx(update.effective_user.id)
    if not context.args:
        if active_repo:
            await update.message.reply_text(
                f"Active: `{active_repo}` on `{active_branch}`", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("Usage: `/repo <name>`", parse_mode="Markdown")
        return
    name = context.args[0]
    try:
        info = gh.get_repo_info(token, username, name)
        update_session(update.effective_user.id, active_repo=name)
        default = info.get("default_branch", "main")
        update_session(update.effective_user.id, active_branch=default)
        await update.message.reply_text(
            f"✅ Active repo: `{name}` on `{default}`", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /repoinfo ─────────────────────────────────────────────────────────────────

@require_login
async def cmd_repoinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        info = gh.get_repo_info(token, username, repo)
        commits = gh.get_latest_commits(token, username, repo, branch, per_page=3)
        commit_lines = "\n".join(
            f"  `{c['sha'][:7]}` {c['commit']['message'].splitlines()[0][:55]}"
            for c in commits
        )
        await update.message.reply_text(
            f"📦 *{info['name']}*\n"
            f"{'🔒 Private' if info['private'] else '🌐 Public'} | "
            f"⭐ {info['stargazers_count']} | 🍴 {info['forks_count']}\n\n"
            f"📝 {info.get('description') or 'No description'}\n"
            f"🌿 Default: `{info['default_branch']}`\n"
            f"🔗 {info['html_url']}\n\n"
            f"*Recent commits:*\n{commit_lines}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /search <query> ───────────────────────────────────────────────────────────

@require_login
async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, _, _, _ = _ctx(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: `/search <query>`", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    try:
        results = gh.search_repos(token, query)
        items = results.get("items", [])
        if not items:
            await update.message.reply_text(f"No repos found for `{query}`", parse_mode="Markdown")
            return
        lines = [f"🔍 *Search: `{query}`*\n"]
        for r in items[:8]:
            lines.append(
                f"• `{r['full_name']}` ⭐{r['stargazers_count']}\n"
                f"  {(r.get('description') or 'No description')[:60]}"
            )
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /branches ─────────────────────────────────────────────────────────────────

@require_login
async def cmd_branches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        branches = gh.get_branches(token, username, repo)
        lines = [f"🌿 *Branches in `{repo}`*\n"]
        for b in branches:
            marker = "👉 " if b["name"] == branch else "   "
            lines.append(f"{marker}`{b['name']}`")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /branch <name> ────────────────────────────────────────────────────────────

@require_login
async def cmd_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, current_branch = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/branch <name>`", parse_mode="Markdown")
        return
    name = context.args[0]
    try:
        existing = [b["name"] for b in gh.get_branches(token, username, repo)]
        if name in existing:
            update_session(update.effective_user.id, active_branch=name)
            await update.message.reply_text(
                f"✅ Switched to `{name}`", parse_mode="Markdown"
            )
        else:
            gh.create_branch(token, username, repo, name, from_branch=current_branch)
            update_session(update.effective_user.id, active_branch=name)
            await update.message.reply_text(
                f"✅ Created and switched to `{name}` (from `{current_branch}`)",
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /files [path] ─────────────────────────────────────────────────────────────

@require_login
async def cmd_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    path = " ".join(context.args) if context.args else ""
    try:
        contents = gh.get_files(token, username, repo, path, branch)
        if isinstance(contents, dict):
            await update.message.reply_text(
                f"📄 `{contents['path']}`\nSize: {contents['size']} bytes\n🔗 {contents['html_url']}",
                parse_mode="Markdown",
            )
            return
        lines = [f"📁 *`{repo}/{path or ''}` on `{branch}`*\n"]
        for f in sorted(contents, key=lambda x: (x["type"] != "dir", x["name"])):
            icon = "📂" if f["type"] == "dir" else "📄"
            suffix = "/" if f["type"] == "dir" else ""
            lines.append(f"{icon} `{f['name']}{suffix}`")
        await update.message.reply_text("\n".join(lines) or "_(empty)_", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /readme ───────────────────────────────────────────────────────────────────

@require_login
async def cmd_readme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        readme = gh.get_readme(token, username, repo)
        import base64
        content = base64.b64decode(readme["content"]).decode("utf-8")
        preview = content[:800] + ("\n\n..._(truncated)_" if len(content) > 800 else "")
        await update.message.reply_text(
            f"📄 *README — {repo}*\n\n{preview}", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /createfile <path> | <content> | <commit msg> ────────────────────────────

@require_login
async def cmd_createfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, branch = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/createfile <path> | <content> | <commit message>`",
            parse_mode="Markdown",
        )
        return
    full = " ".join(context.args)
    parts = [p.strip() for p in full.split("|")]
    if len(parts) < 2:
        await update.message.reply_text("Provide at least: `<path> | <content>`", parse_mode="Markdown")
        return
    path = parts[0]
    content = parts[1]
    message = parts[2] if len(parts) > 2 else f"Add {path} via GIT KING Bot"
    try:
        result = gh.create_file(token, username, repo, path, content, message, branch)
        await update.message.reply_text(
            f"✅ File created: `{path}`\n🔗 {result['content']['html_url']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /findfile <filename> ──────────────────────────────────────────────────────

@require_login
async def cmd_findfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/findfile <filename>`", parse_mode="Markdown")
        return
    filename = " ".join(context.args)
    try:
        results = gh.search_code(token, filename, owner=username, repo=repo)
        items = results.get("items", [])
        if not items:
            await update.message.reply_text(f"No files matching `{filename}` found.", parse_mode="Markdown")
            return
        lines = [f"🔍 *Files matching `{filename}`*\n"]
        for item in items[:10]:
            lines.append(f"📄 `{item['path']}`\n   🔗 {item['html_url']}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /issues ───────────────────────────────────────────────────────────────────

@require_login
async def cmd_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        issues = gh.get_issues(token, username, repo)
        if not issues:
            await update.message.reply_text(f"✅ No open issues in `{repo}`", parse_mode="Markdown")
            return
        lines = [f"🐛 *Open Issues — {repo}*\n"]
        for i in issues:
            lines.append(f"#{i['number']} — {i['title']}\n   🔗 {i['html_url']}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /newissue <title> | <body> ────────────────────────────────────────────────

@require_login
async def cmd_newissue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/newissue <title> | <body>`", parse_mode="Markdown"
        )
        return
    full = " ".join(context.args)
    parts = full.split("|", 1)
    title = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    try:
        issue = gh.create_issue(token, username, repo, title, body)
        await update.message.reply_text(
            f"✅ Issue *#{issue['number']}* created\n{issue['title']}\n🔗 {issue['html_url']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /closeissue <number> ──────────────────────────────────────────────────────

@require_login
async def cmd_closeissue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/closeissue <number>`", parse_mode="Markdown")
        return
    try:
        issue = gh.close_issue(token, username, repo, int(context.args[0]))
        await update.message.reply_text(
            f"✅ Issue *#{issue['number']}* closed.", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /prs ──────────────────────────────────────────────────────────────────────

@require_login
async def cmd_prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    try:
        prs = gh.get_pull_requests(token, username, repo)
        if not prs:
            await update.message.reply_text(f"✅ No open PRs in `{repo}`", parse_mode="Markdown")
            return
        lines = [f"🔀 *Open PRs — {repo}*\n"]
        for pr in prs:
            lines.append(
                f"#{pr['number']} — {pr['title']}\n"
                f"   `{pr['head']['ref']}` → `{pr['base']['ref']}`\n"
                f"   🔗 {pr['html_url']}"
            )
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /merge <number> ───────────────────────────────────────────────────────────

@require_login
async def cmd_merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/merge <pr_number>`", parse_mode="Markdown")
        return
    try:
        result = gh.merge_pr(token, username, repo, int(context.args[0]))
        await update.message.reply_text(
            f"✅ PR #{context.args[0]} merged!\n{result.get('message', '')}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


# ── /invite <username> ────────────────────────────────────────────────────────

@require_login
async def cmd_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token, username, repo, _ = _ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text("Set a repo first: `/repo <name>`", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/invite <github_username>`", parse_mode="Markdown")
        return
    invitee = context.args[0]
    try:
        status = gh.add_collaborator(token, username, repo, invitee)
        if status in (201, 204):
            await update.message.reply_text(
                f"✅ Invitation sent to `{invitee}` for `{repo}`", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"Response code: {status}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
