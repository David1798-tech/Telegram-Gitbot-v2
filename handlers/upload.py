import io
import base64
import zipfile
from telegram import Update
from telegram.ext import ContextTypes
from auth import require_login, get_user_ctx
from services import github_api as gh

SKIP = {"__MACOSX", ".DS_Store", ".git"}


def _should_skip(name):
    if name.endswith("/"):
        return True
    for bad in SKIP:
        if bad in name:
            return True
    return False


def _strip_root(names):
    """Strip common top-level folder prefix if all files share one."""
    parts = [n.split("/") for n in names]
    if all(len(p) > 1 for p in parts):
        root = parts[0][0]
        if all(p[0] == root for p in parts):
            return root + "/"
    return ""


@require_login
async def handle_zip_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return

    fname = doc.file_name or ""
    if not (fname.endswith(".zip") or doc.mime_type in ("application/zip", "application/x-zip-compressed")):
        await update.message.reply_text(
            "Send a `.zip` file to push its contents to your active repo.",
            parse_mode="Markdown",
        )
        return

    token, username, repo, branch = get_user_ctx(update.effective_user.id)
    if not repo:
        await update.message.reply_text(
            "Set a repo first with `/repo <name>` then resend the zip.",
            parse_mode="Markdown",
        )
        return

    msg = await update.message.reply_text(
        f"📦 `{fname}`\n🔄 Downloading...", parse_mode="Markdown"
    )

    try:
        # Download
        tg_file = await context.bot.get_file(doc.file_id)
        zip_bytes = await tg_file.download_as_bytearray()

        await msg.edit_text(f"📦 `{fname}`\n🔄 Extracting files...", parse_mode="Markdown")

        # Extract
        files_dict = {}
        with zipfile.ZipFile(io.BytesIO(bytes(zip_bytes))) as zf:
            names = [n for n in zf.namelist() if not _should_skip(n)]
            prefix = _strip_root(names)

            for name in names:
                clean_path = name[len(prefix):] if prefix else name
                if not clean_path:
                    continue
                raw = zf.read(name)
                try:
                    files_dict[clean_path] = {
                        "content": raw.decode("utf-8"),
                        "encoding": "utf-8",
                    }
                except UnicodeDecodeError:
                    # Binary file — base64
                    files_dict[clean_path] = {
                        "content": base64.b64encode(raw).decode("ascii"),
                        "encoding": "base64",
                    }

        if not files_dict:
            await msg.edit_text("❌ No pushable files found in the zip.")
            return

        file_count = len(files_dict)
        await msg.edit_text(
            f"📦 `{fname}`\n🔄 Pushing {file_count} file(s) to `{repo}/{branch}`...",
            parse_mode="Markdown",
        )

        # Push all files in one commit
        commit_url = gh.push_files_batch(
            token, username, repo, branch, files_dict,
            message=f"Upload {fname} via GIT KING Bot",
        )

        # Build file list preview (max 10)
        preview = "\n".join(f"  `{p}`" for p in list(files_dict.keys())[:10])
        if file_count > 10:
            preview += f"\n  _...and {file_count - 10} more_"

        await msg.edit_text(
            f"✅ *{file_count} file(s) pushed to `{repo}`*\n\n"
            f"Branch: `{branch}`\n\n"
            f"*Files:*\n{preview}\n\n"
            f"🔗 {commit_url}",
            parse_mode="Markdown",
        )

    except zipfile.BadZipFile:
        await msg.edit_text("❌ That file isn't a valid zip archive.")
    except Exception as e:
        await msg.edit_text(f"❌ Upload failed: {e}")
