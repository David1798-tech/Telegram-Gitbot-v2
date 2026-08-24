<div align="center">

# 🤖 GIT KING Bot

**GitHub repo management, CI workflows, and multi-platform deploys — all from Telegram**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Made by Mr Syco](https://img.shields.io/badge/made%20by-Mr%20Syco-6E9EFF)](https://github.com/Sycosmile)

</div>

A Telegram bot that puts GitHub repo management, CI workflows, and multi-platform deploys in your chat — browse repos, manage issues/PRs, push files, trigger deployments, and get notified on new activity, all without leaving Telegram.

## Features

**GitHub**
- `/login <pat>` / `/logout` / `/me` — connect your GitHub account (your token message is deleted immediately for security)
- `/repos`, `/repo <name>`, `/repoinfo`, `/search <query>` — browse and select repos
- `/branches`, `/branch <name>` — list or switch/create branches
- `/files [path]`, `/readme`, `/createfile <path> | <content> | <msg>`, `/findfile <name>` — browse and edit repo contents
- `/issues`, `/newissue <title> | <body>`, `/closeissue <n>` — issue management
- `/prs`, `/merge <n>` — pull request management
- `/invite <username>` — add a collaborator
- Zip upload — send a `.zip` to push multiple files in one commit via the Git Trees API

**Stats & Workflows**
- `/stats`, `/traffic` — contributor and traffic stats
- `/workflows`, `/runworkflow`, `/wlogs` — trigger and inspect GitHub Actions runs

**Deploy**
- `/deploy <vercel|render|netlify|fly>` — trigger a deployment on any connected platform
- `/deploystatus` — check the latest deploy status

**Watch & Notify**
- `/watch <owner/repo>`, `/unwatch`, `/watching` — get notified of new commits/issues/PRs on watched repos
- Background polling (interval configurable) plus a daily digest at a configured time

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/Sycosmile/Telegram-Gitbot-v2.git
   cd Telegram-Gitbot-v2
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with:
   ```
   TELEGRAM_TOKEN=your_bot_token

   # Deploy platform credentials (per-bot owner, optional — only needed
   # for the platforms you actually want /deploy to support)
   VERCEL_TOKEN=
   VERCEL_PROJECT_ID=
   VERCEL_DEPLOY_HOOK=
   RENDER_API_KEY=
   RENDER_SERVICE_ID=
   RENDER_DEPLOY_HOOK=
   NETLIFY_TOKEN=
   NETLIFY_SITE_ID=
   NETLIFY_DEPLOY_HOOK=
   FLY_API_TOKEN=
   FLY_APP_NAME=

   # Optional scheduling
   DIGEST_HOUR=8
   DIGEST_MINUTE=0
   POLL_INTERVAL=300
   ```

4. Run it:
   ```bash
   python bot.py
   ```

Each user connects their own GitHub account via `/login <personal_access_token>` — the bot owner's `.env` credentials are only used for the deploy-platform integrations, not for GitHub access.

## Security notes

- GitHub tokens are stored per-user in a local SQLite database (`gitbot.db`), which is gitignored — never commit it.
- The `/login` command deletes your message containing the token immediately after receiving it.
- Only use `/login` in a private chat with the bot, never in a group.

## License

MIT — see `LICENSE` for details.

## Author

Built by **MR SYCO** — [@Sycosmile](https://github.com/Sycosmile) on GitHub and X.
