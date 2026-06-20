# Repository Guidelines

## Project Structure & Module Organization

This repository powers “今乐福”, a Flask API plus static frontend for LOF arbitrage data. `app.py` exports the Flask `app` and route table. `api/index.py` is a thin adapter that imports the same app. Core Jisilu fetching, parsing, and filtering logic lives in `lof_lib.py`. Frontend assets live under `public/`, with `public/index.html` as the main page and images/SVGs beside it. Bark push helpers for the Aliyun/BaoTa environment are named `baota_lof_*_push.py` and `baota_lof_*_cron.sh`. There is currently no dedicated `tests/` directory.

## Build, Test, and Development Commands

Install dependencies:

```bash
pip3 install -r requirements.txt
```

Run the local API:

```bash
flask --app app run --port 5003
```

Useful smoke checks:

```bash
curl http://127.0.0.1:5003/api/health
curl http://127.0.0.1:5003/api/lof
```

`public/index.html` can be opened directly or served by nginx/static hosting. Production deployment defaults to Aliyun/BaoTa/nginx, not Vercel.

## Coding Style & Naming Conventions

Use Python 3, 4-space indentation, type hints where they improve clarity, and small request-scoped helpers for API work. Keep route behavior in `app.py` and reusable data logic in `lof_lib.py`. Prefer descriptive snake_case names for Python functions and variables. Keep static files in `public/`; do not introduce Flask `static_folder` usage.

## Testing Guidelines

No formal test framework is configured. For changes, run at least the Flask server and the smoke checks above. For data-source changes, verify both authenticated and degraded Jisilu behavior when possible. For history changes, test `/api/lof/<fund_id>/history` with and without `TUSHARE_TOKEN`.

## Commit & Pull Request Guidelines

Recent history uses short imperative or Conventional Commit-style messages, for example `feat: ...`, `fix: ...`, and `docs: ...`. Keep commits focused. Pull requests should describe the user-visible change, list any API or environment-variable impact, include screenshots for frontend changes, and note the smoke checks performed.

## Security & Configuration Tips

Configure secrets through environment variables such as `JISILU_USERNAME`, `JISILU_PASSWORD`, `JISILU_COOKIE`, and `TUSHARE_TOKEN`. Never commit real cookies, tokens, passwords, or BaoTa/server credentials. Do not reintroduce `database.py`, `scheduler.py`, SQLite persistence, APScheduler, or long-running background schedulers.
