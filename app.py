#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今乐福 - Flask API.

This entrypoint intentionally avoids local SQLite files, APScheduler, and
long-running background processes.
"""

import os
import re
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from html import unescape
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import requests
from flask import Flask, jsonify, request

from lof_lib import JisiluAPI, filter_lof

load_dotenv()

app = Flask(__name__)

TUSHARE_API_URL = "http://api.tushare.pro"
TUSHARE_TIMEOUT = 12
EASTMONEY_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
EASTMONEY_NAV_URL = "https://fundf10.eastmoney.com/F10DataApi.aspx"
EASTMONEY_TIMEOUT = 12
TENCENT_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"


def _api_client() -> JisiluAPI:
    """Create a request-scoped Jisilu client using environment configuration."""
    return JisiluAPI(
        cookie=os.environ.get("JISILU_COOKIE"),
        username=os.environ.get("JISILU_USERNAME"),
        password=os.environ.get("JISILU_PASSWORD"),
    )


def _success_response(data, api: JisiluAPI):
    return jsonify(
        {
            "success": True,
            "data": [asdict(lof) for lof in data],
            "total": len(data),
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "auth_status": api.get_auth_status(),
        }
    )


def _today_yyyymmdd() -> str:
    return datetime.now().strftime("%Y%m%d")


def _history_start_date(range_key: str) -> str:
    windows = {
        "1w": 14,
        "1m": 45,
        "3m": 120,
        "1y": 370,
    }
    days = windows.get(range_key, windows["1y"])
    return (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")


def _fund_ts_code(fund_id: str) -> str:
    clean_id = "".join(ch for ch in fund_id if ch.isdigit())
    if len(clean_id) != 6:
        raise ValueError("基金代码格式不正确")

    if clean_id.startswith(("50", "51", "52", "56", "58")):
        return f"{clean_id}.SH"
    if clean_id.startswith(("15", "16", "18")):
        return f"{clean_id}.SZ"

    raise ValueError(f"无法判断 {clean_id} 的交易所后缀")


def _clean_fund_id(fund_id: str) -> str:
    clean_id = "".join(ch for ch in fund_id if ch.isdigit())
    if len(clean_id) != 6:
        raise ValueError("基金代码格式不正确")
    return clean_id


def _eastmoney_market_prefix(fund_id: str) -> str:
    clean_id = _clean_fund_id(fund_id)
    if clean_id.startswith(("50", "51", "52", "56", "58")):
        return "1"
    if clean_id.startswith(("15", "16", "18")):
        return "0"
    raise ValueError(f"无法判断 {clean_id} 的交易所前缀")


def _tencent_symbol(fund_id: str) -> str:
    clean_id = _clean_fund_id(fund_id)
    if clean_id.startswith(("50", "51", "52", "56", "58")):
        return f"sh{clean_id}"
    if clean_id.startswith(("15", "16", "18")):
        return f"sz{clean_id}"
    raise ValueError(f"无法判断 {clean_id} 的交易所前缀")


def _tushare_call(
    api_name: str,
    params: Dict[str, Any],
    fields: str,
    token: str,
) -> List[Dict[str, Any]]:
    response = requests.post(
        TUSHARE_API_URL,
        json={
            "api_name": api_name,
            "token": token,
            "params": params,
            "fields": fields,
        },
        timeout=TUSHARE_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("code") != 0:
        msg = payload.get("msg") or "Tushare API 调用失败"
        raise RuntimeError(msg)

    data = payload.get("data") or {}
    field_names = data.get("fields") or []
    items = data.get("items") or []
    return [dict(zip(field_names, item)) for item in items]


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "-", "--"):
        return None
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _yyyymmdd_to_iso(value: str) -> str:
    text = str(value or "")
    if len(text) == 8:
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def _iso_to_yyyymmdd(value: str) -> str:
    return str(value or "").replace("-", "")


def _normalize_price_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for row in rows:
        trade_date = str(row.get("trade_date") or "")
        if len(trade_date) != 8:
            continue
        normalized.append(
            {
                "date": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}",
                "raw_date": trade_date,
                "open": _to_float(row.get("open")),
                "high": _to_float(row.get("high")),
                "low": _to_float(row.get("low")),
                "close": _to_float(row.get("close")),
                "pct_chg": _to_float(row.get("pct_chg")),
                "vol": _to_float(row.get("vol")),
                "amount": _to_float(row.get("amount")),
            }
        )
    return sorted(normalized, key=lambda item: item["raw_date"])


def _normalize_nav_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for row in rows:
        nav_date = str(row.get("nav_date") or "")
        if len(nav_date) != 8:
            continue
        normalized.append(
            {
                "date": f"{nav_date[:4]}-{nav_date[4:6]}-{nav_date[6:]}",
                "raw_date": nav_date,
                "ann_date": row.get("ann_date"),
                "unit_nav": _to_float(row.get("unit_nav")),
                "accum_nav": _to_float(row.get("accum_nav")),
                "adj_nav": _to_float(row.get("adj_nav")),
            }
        )
    return sorted(normalized, key=lambda item: item["raw_date"])


def _eastmoney_price_rows(fund_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    clean_id = _clean_fund_id(fund_id)
    response = requests.get(
        EASTMONEY_KLINE_URL,
        params={
            "secid": f"{_eastmoney_market_prefix(clean_id)}.{clean_id}",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": _iso_to_yyyymmdd(start_date),
            "end": _iso_to_yyyymmdd(end_date),
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=EASTMONEY_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}

    rows = []
    for item in data.get("klines") or []:
        parts = str(item).split(",")
        if len(parts) < 11:
            continue
        trade_date = parts[0].replace("-", "")
        amount_yuan = _to_float(parts[6])
        rows.append(
            {
                "trade_date": trade_date,
                "open": parts[1],
                "close": parts[2],
                "high": parts[3],
                "low": parts[4],
                "vol": parts[5],
                # Keep the same unit as Tushare fund_daily amount: thousand yuan.
                "amount": amount_yuan / 1000 if amount_yuan is not None else None,
                "pct_chg": parts[8],
            }
        )

    return _normalize_price_rows(rows)


def _tencent_price_rows(fund_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    symbol = _tencent_symbol(fund_id)
    response = requests.get(
        TENCENT_KLINE_URL,
        params={"param": f"{symbol},day,,,420,qfq"},
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"},
        timeout=EASTMONEY_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    data = (payload.get("data") or {}).get(symbol) or {}

    rows = []
    previous_close = None
    start_raw = _iso_to_yyyymmdd(start_date)
    end_raw = _iso_to_yyyymmdd(end_date)

    for item in data.get("day") or []:
        if len(item) < 6:
            continue
        trade_date = str(item[0]).replace("-", "")
        close = _to_float(item[2])
        volume_lots = _to_float(item[5])
        if previous_close and close is not None:
            pct_chg = (close / previous_close - 1) * 100
        else:
            pct_chg = None
        previous_close = close if close is not None else previous_close

        if trade_date < start_raw or trade_date > end_raw:
            continue

        amount = None
        if volume_lots is not None and close is not None:
            amount = volume_lots * close * 100 / 1000

        rows.append(
            {
                "trade_date": trade_date,
                "open": item[1],
                "close": item[2],
                "high": item[3],
                "low": item[4],
                "vol": volume_lots,
                "amount": amount,
                "pct_chg": pct_chg,
            }
        )

    return _normalize_price_rows(rows)


def _public_price_rows(fund_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    try:
        rows = _eastmoney_price_rows(fund_id, start_date, end_date)
        if rows:
            return rows
    except Exception as exc:
        print(f"[history] eastmoney price fallback to tencent: {exc}")
    return _tencent_price_rows(fund_id, start_date, end_date)


def _extract_table_rows(html_text: str) -> List[List[str]]:
    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", html_text, flags=re.I | re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.I | re.S)
        if not cells:
            continue
        cleaned = []
        for cell in cells:
            text = re.sub(r"<[^>]+>", "", cell)
            cleaned.append(unescape(text).strip())
        rows.append(cleaned)
    return rows


def _eastmoney_nav_rows(fund_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    clean_id = _clean_fund_id(fund_id)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://fundf10.eastmoney.com/jjjz_{clean_id}.html",
    }
    rows = []
    seen_dates = set()
    pages = 1

    for page in range(1, 31):
        response = requests.get(
            EASTMONEY_NAV_URL,
            params={
                "type": "lsjz",
                "code": clean_id,
                "page": str(page),
                "per": "20",
                "sdate": _yyyymmdd_to_iso(start_date),
                "edate": _yyyymmdd_to_iso(end_date),
            },
            headers=headers,
            timeout=EASTMONEY_TIMEOUT,
        )
        response.raise_for_status()

        page_match = re.search(r"pages:(\d+)", response.text)
        if page_match:
            pages = max(1, int(page_match.group(1)))

        for cells in _extract_table_rows(response.text):
            if len(cells) < 3 or not re.match(r"^\d{4}-\d{2}-\d{2}$", cells[0]):
                continue
            nav_date = cells[0].replace("-", "")
            if nav_date in seen_dates:
                continue
            seen_dates.add(nav_date)
            rows.append(
                {
                    "nav_date": nav_date,
                    "ann_date": None,
                    "unit_nav": cells[1],
                    "accum_nav": cells[2],
                    "adj_nav": None,
                }
            )

        if page >= pages:
            break

    return _normalize_nav_rows(rows)


def _eastmoney_history_response(
    fund_id: str,
    range_key: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    price_rows = _public_price_rows(fund_id, start_date, end_date)
    nav_rows = _eastmoney_nav_rows(fund_id, start_date, end_date)
    if not price_rows and not nav_rows:
        raise RuntimeError("东方财富未返回可用历史价格或净值数据")

    return {
        "success": True,
        "fund_id": _clean_fund_id(fund_id),
        "ts_code": None,
        "range": range_key,
        "start_date": _iso_to_yyyymmdd(start_date),
        "end_date": _iso_to_yyyymmdd(end_date),
        "price": price_rows,
        "nav": nav_rows,
        "comparison": _merge_history(price_rows, nav_rows),
        "source": "eastmoney",
        "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _merge_history(
    price_rows: List[Dict[str, Any]],
    nav_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    comparison = []
    nav_index = 0
    latest_nav: Optional[Dict[str, Any]] = None

    for price in price_rows:
        while nav_index < len(nav_rows) and nav_rows[nav_index]["raw_date"] <= price["raw_date"]:
            latest_nav = nav_rows[nav_index]
            nav_index += 1

        close = price.get("close")
        unit_nav = latest_nav.get("unit_nav") if latest_nav else None
        premium = None
        if close and unit_nav:
            premium = (close / unit_nav - 1) * 100

        comparison.append(
            {
                "date": price["date"],
                "close": close,
                "pct_chg": price.get("pct_chg"),
                "amount": price.get("amount"),
                "unit_nav": unit_nav,
                "nav_date": latest_nav.get("date") if latest_nav else None,
                "premium": premium,
            }
        )

    return comparison


@app.get("/api/health")
def health():
    """Lightweight health check that does not call external data sources."""
    return jsonify(
        {
            "success": True,
            "service": "happy-lof",
            "runtime": "flask",
            "has_jisilu_cookie": bool(os.environ.get("JISILU_COOKIE")),
            "has_jisilu_dynamic_login": bool(
                os.environ.get("JISILU_USERNAME") and os.environ.get("JISILU_PASSWORD")
            ),
        }
    )


@app.get("/api/lof")
def get_lof_data():
    """Return real-time LOF data. The browser applies display filters."""
    api = _api_client()
    try:
        all_lof = api.get_all_lof()
        filtered = filter_lof(
            all_lof,
            min_premium=-100,
            min_volume=0,
            only_limited=False,
        )
        return _success_response(filtered, api)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.get("/api/lof/<fund_id>/history")
def get_lof_history(fund_id: str):
    """Return on-demand LOF exchange price and NAV history."""
    range_key = request.args.get("range", "1y")
    start_date = request.args.get("start_date") or _history_start_date(range_key)
    end_date = request.args.get("end_date") or _today_yyyymmdd()
    token = os.environ.get("TUSHARE_TOKEN") or os.environ.get("TUSHARE_PRO_TOKEN")

    try:
        if not token:
            return jsonify(_eastmoney_history_response(fund_id, range_key, start_date, end_date))

        ts_code = _fund_ts_code(fund_id)
        price_rows = _normalize_price_rows(
            _tushare_call(
                "fund_daily",
                {
                    "ts_code": ts_code,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
                token,
            )
        )
        nav_rows = _normalize_nav_rows(
            _tushare_call(
                "fund_nav",
                {
                    "ts_code": ts_code,
                    "start_date": start_date,
                    "end_date": end_date,
                    "market": "E",
                },
                "ts_code,ann_date,nav_date,unit_nav,accum_nav,accum_div,net_asset,total_netasset,adj_nav",
                token,
            )
        )

        return jsonify(
            {
                "success": True,
                "fund_id": fund_id,
                "ts_code": ts_code,
                "range": range_key,
                "start_date": start_date,
                "end_date": end_date,
                "price": price_rows,
                "nav": nav_rows,
                "comparison": _merge_history(price_rows, nav_rows),
                "source": "tushare",
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as exc:
        if token:
            try:
                return jsonify(_eastmoney_history_response(fund_id, range_key, start_date, end_date))
            except Exception:
                pass
        return jsonify({"success": False, "error": str(exc)}), 502


@app.get("/api/lof/all")
def get_all_lof_data():
    """Return all currently limited or paused LOF data sorted by premium."""
    api = _api_client()
    try:
        all_lof = api.get_all_lof()
        filtered = filter_lof(all_lof, only_limited=True)
        return _success_response(filtered, api)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5003"))
    app.run(host="127.0.0.1", port=port, debug=True)
