#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOF 基金套利提醒脚本 - 腾讯行情 + 东方财富申购状态版

数据源：
1. 东方财富 clist：获取场内 LOF/FJ 代码池
2. 腾讯财经行情：获取场内价格、涨幅、成交额、净值、溢价率
3. 东方财富申购状态：获取申购状态、购买起点、日累计限定金额

筛选口径：
- 实时溢价率 >= 1%
- 成交额 >= 1000 万
- 申购状态不能是暂停申购
- 日累计限定金额不是无限额，或申购状态包含“限”

说明：
- 腾讯行情里的净值是最新公布净值，不是盘中实时估值。
- 该脚本不读取集思录 Cookie。
"""

import datetime
import json
import logging
import re
import sys
import time
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).parent.absolute()
LOG_FILE = SCRIPT_DIR / "lof_tencent_eastmoney_push.log"
PROJECT_URL = "http://8.134.134.156/happy-lof/"

EASTMONEY_CLIST_URLS = (
    "https://88.push2.eastmoney.com/api/qt/clist/get",
    "https://push2.eastmoney.com/api/qt/clist/get",
)
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q=%s"
EASTMONEY_PURCHASE_URL = "https://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx"
UNLIMITED_AMOUNT = 100000000000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def load_config():
    config_file = SCRIPT_DIR / "config.json"
    if not config_file.exists():
        logging.error("配置文件不存在: %s", config_file)
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logging.error("读取配置文件失败: %s", exc)
        return {}


def parse_float(value):
    if value is None:
        return 0.0
    try:
        clean_value = str(value).replace(",", "").strip()
        if clean_value in ("", "-", "--"):
            return 0.0
        return float(clean_value)
    except Exception:
        return 0.0


def format_money_wan(value):
    if value >= 10000:
        return "%.2f亿" % (value / 10000)
    return "%.0f万" % value


def format_limit(value):
    if value >= UNLIMITED_AMOUNT:
        return "无限额"
    if value >= 10000:
        return "限%.0f万" % (value / 10000)
    if value > 0:
        return "限%.0f元" % value
    return "未知"


def market_code(code):
    if code.startswith(("50", "51", "52", "56", "58")):
        return "sh" + code
    return "sz" + code


class TencentEastmoneyLofPush:
    def __init__(self, config):
        lof_config = config.get("lof_tencent_eastmoney", {}) or config.get("lof", {})
        self.bark_url = (
            lof_config.get("bark_url")
            or config.get("newbond", {}).get("bark_url")
            or ""
        ).rstrip("/")
        self.min_premium = float(lof_config.get("min_premium", 1.0))
        self.min_volume = float(lof_config.get("min_volume", 1000))
        self.max_items = int(lof_config.get("max_items", 10))

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

    def get_json_with_retry(self, url, params, referer=None, retries=3, timeout=20):
        headers = {}
        if referer:
            headers["Referer"] = referer
        last_error = None
        for index in range(retries):
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                logging.warning("请求失败，重试 %s/%s: %s", index + 1, retries, exc)
                time.sleep(0.6 + index * 0.8)
        raise RuntimeError("请求失败: %s" % last_error)

    def get_lof_codes(self):
        codes = []
        total = None
        fields = "f12"
        for page in range(1, 12):
            params = {
                "pn": str(page),
                "pz": "100",
                "po": "1",
                "np": "1",
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": "2",
                "invt": "2",
                "fid": "f3",
                "fs": "b:MK0404,b:MK0405,b:MK0406,b:MK0407",
                "fields": fields,
            }

            data = None
            for url in EASTMONEY_CLIST_URLS:
                try:
                    data = self.get_json_with_retry(url, params, referer="https://quote.eastmoney.com/")
                    break
                except Exception as exc:
                    logging.warning("代码池接口不可用 %s: %s", url, exc)
            if not data:
                raise RuntimeError("无法获取 LOF 代码池")

            payload = data.get("data") or {}
            total = payload.get("total") or total
            rows = payload.get("diff") or []
            if not rows:
                break
            for row in rows:
                code = str(row.get("f12") or "").strip()
                if code and code not in codes:
                    codes.append(code)
            if total and len(codes) >= int(total):
                break

        logging.info("获取 LOF/FJ 代码 %d 个，接口 total=%s", len(codes), total)
        return codes

    def get_lof_codes_from_purchase(self, purchase):
        prefixes = ("15", "16", "18", "50", "51", "52", "56", "58")
        codes = sorted(code for code in purchase.keys() if code.startswith(prefixes))
        logging.info("从申购状态表生成候选代码 %d 个", len(codes))
        return codes

    def get_quotes(self, codes):
        quotes = {}
        for start in range(0, len(codes), 40):
            batch = codes[start:start + 40]
            query = ",".join(market_code(code) for code in batch)
            url = TENCENT_QUOTE_URL % query
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            response.encoding = "gbk"

            for line in response.text.strip().split(";"):
                if "=\"" not in line:
                    continue
                parts = line.split("=\"", 1)[1].rsplit("\"", 1)[0].split("~")
                if len(parts) < 82 or not parts[2]:
                    continue
                if parts[61] not in ("LOF", "FJ"):
                    continue
                code = parts[2]
                quotes[code] = {
                    "fund_id": code,
                    "fund_name": parts[1],
                    "price": parse_float(parts[3]),
                    "change_pct": parse_float(parts[32]),
                    "volume": parse_float(parts[57]),  # 成交额，万元
                    "net_value": parse_float(parts[81]),
                    "premium_rate": parse_float(parts[77]),
                    "quote_time": parts[30],
                }
            time.sleep(0.05)

        logging.info("获取腾讯行情 %d 条", len(quotes))
        return quotes

    def get_purchase_status(self):
        params = {
            "t": "8",
            "page": "1,30000",
            "js": "reData",
            "sort": "fcode,asc",
        }
        response = self.session.get(
            EASTMONEY_PURCHASE_URL,
            params=params,
            headers={"Referer": "https://fund.eastmoney.com/Fund_sgzt.html"},
            timeout=60,
        )
        response.raise_for_status()
        response.encoding = "utf-8"

        result = {}
        for match in re.finditer(r'\[("\d{6}".*?)]', response.text):
            try:
                row = json.loads("[" + match.group(1) + "]")
            except Exception:
                continue
            if len(row) < 13:
                continue
            result[row[0]] = {
                "full_name": row[1],
                "fund_type": row[2],
                "nav": parse_float(row[3]),
                "nav_date": row[4],
                "apply_status": row[5],
                "redeem_status": row[6],
                "next_open_date": row[7],
                "min_purchase": parse_float(row[8]),
                "daily_limit": parse_float(row[9]),
                "fee": row[12],
            }

        logging.info("获取东方财富申购状态 %d 条", len(result))
        return result

    def get_targets(self):
        purchase = self.get_purchase_status()
        try:
            codes = self.get_lof_codes()
        except Exception as exc:
            logging.warning("代码池接口失败，改用申购状态表候选代码: %s", exc)
            codes = self.get_lof_codes_from_purchase(purchase)
        quotes = self.get_quotes(codes)

        targets = []
        for code, quote in quotes.items():
            status = purchase.get(code, {})
            apply_status = status.get("apply_status", "")
            daily_limit = parse_float(status.get("daily_limit"))
            is_unlimited = daily_limit >= UNLIMITED_AMOUNT
            is_limited = (0 < daily_limit < UNLIMITED_AMOUNT) or ("限" in apply_status)

            if "暂停" in apply_status:
                continue
            if not is_limited or is_unlimited:
                continue
            if quote["premium_rate"] < self.min_premium:
                continue
            if quote["volume"] < self.min_volume:
                continue

            merged = dict(quote)
            merged.update(status)
            merged["limit_text"] = format_limit(daily_limit)
            targets.append(merged)

        return sorted(targets, key=lambda item: item["premium_rate"], reverse=True)

    def build_message(self, targets):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        shown = targets[:self.max_items]
        summary_parts = [
            "%s %.2f%% %s" % (
                fund["fund_name"],
                fund["premium_rate"],
                fund.get("limit_text") or "未知",
            )
            for fund in shown
        ]
        lines = [
            "\n".join(summary_parts),
            "",
        ]

        for index, fund in enumerate(shown, 1):
            change_sign = "+" if fund["change_pct"] > 0 else ""
            lines.append(
                "%d. %s（%s）\n"
                "价格：%.3f（%s%.2f%%）｜净值：%.4f\n"
                "成交额：%s｜实时溢价率：%.2f%%\n"
                "申购状态：%s｜日限额：%s"
                % (
                    index,
                    fund["fund_name"],
                    fund["fund_id"],
                    fund["price"],
                    change_sign,
                    fund["change_pct"],
                    fund["net_value"],
                    format_money_wan(fund["volume"]),
                    fund["premium_rate"],
                    fund.get("apply_status") or "未知",
                    fund.get("limit_text") or "未知",
                )
            )

        if len(targets) > len(shown):
            lines.append("")
            lines.append("还有 %d 只未展示。" % (len(targets) - len(shown)))

        lines.append("")
        lines.append(
            "筛选：溢价>=%.2f%% + 成交额>=%.0f万 + 非暂停申购 + 有日限额"
            % (self.min_premium, self.min_volume)
        )
        lines.append("注：净值为腾讯行情返回的最新公布净值，非盘中估值。")
        lines.append("")
        lines.append(PROJECT_URL)
        return "\n".join(lines)

    def send_msg(self, content, title="LOF套利提醒"):
        if not self.bark_url:
            logging.error("未配置 Bark 推送地址，请在 config.json 中配置 lof_tencent_eastmoney.bark_url 或 newbond.bark_url")
            return False

        bark_url = self.bark_url
        params = {
            "title": title,
            "body": content,
            "url": PROJECT_URL,
            "automaticallyCopy": "1",
            "copy": content,
        }
        response = self.session.get(bark_url, params=params, timeout=15)
        if response.status_code != 200:
            logging.error("Bark 请求失败，状态码: %s", response.status_code)
            return False
        try:
            result = response.json()
        except Exception:
            logging.error("Bark 返回不是 JSON: %s", response.text[:200])
            return False
        if result.get("code") == 200:
            logging.info("Bark 消息发送成功")
            return True
        logging.error("Bark 消息发送失败: %s", result)
        return False

    def push_msg(self, dry_run=False):
        today = datetime.datetime.now()
        if today.weekday() >= 5:
            logging.info("今天是周末（%s），不发送 Bark 推送", today.strftime("%Y-%m-%d"))
            return []

        logging.info("开始检查 LOF 套利机会（腾讯+东财）")
        targets = self.get_targets()
        if not targets:
            logging.info("暂无符合条件的 LOF 套利机会，不发送消息")
            return []

        content = self.build_message(targets)
        logging.info("发现 LOF 套利候选:\n%s", content)
        if not dry_run:
            self.send_msg(content, title="LOF套利提醒｜共 %d 只候选" % len(targets))
        else:
            logging.info("dry-run 模式，不发送 Bark")
        return targets


def main():
    logging.info("=" * 50)
    logging.info("LOF 基金套利提醒任务开始（腾讯+东财）")
    config = load_config()
    dry_run = "--dry-run" in sys.argv
    TencentEastmoneyLofPush(config).push_msg(dry_run=dry_run)
    logging.info("=" * 50)


if __name__ == "__main__":
    main()
