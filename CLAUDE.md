# CLAUDE.md

This repository is the Alibaba Cloud oriented version of Happy LOF.

## Architecture

- `app.py`: Flask API entrypoint for local debugging or server-side mounting.
- `lof_lib.py`: Jisilu data fetching, parsing, and filtering logic.
- `public/index.html`: static frontend page.
- `public/chicken.png`: static icon asset.

The app intentionally avoids local SQLite storage, APScheduler, and long-running local servers. Historical LOF detail data is fetched on demand from Tushare. Production access should go through the Alibaba Cloud nginx deployment, not Vercel.

## Commands

```bash
pip3 install -r requirements.txt
python3 -m py_compile app.py lof_lib.py
flask --app app run --port 5003
```

## API

- `GET /api/health`
- `GET /api/lof`
- `GET /api/lof/all`
- `GET /api/lof/<fund_id>/history`

The history API requires `TUSHARE_TOKEN`; the realtime list continues to work without it.
