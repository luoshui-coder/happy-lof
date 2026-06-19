#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOF 基金套利提醒脚本 - 宝塔面板版

功能：
1. 获取集思录 LOF 实时数据
2. 使用当前项目首页“有利可套”的筛选条件：
   - 申购状态包含“限”
   - 实时溢价率 >= 1%
   - 成交额 >= 1000 万
3. 发现标的后通过 Bark 推送到 iOS 设备

配置方式：
  默认复用同目录 config.json 中 newbond.bark_url。
  也可以单独增加 lof 配置：
  {
    "lof": {
      "bark_url": "https://api.day.app/xxxx",
      "jisilu_cookie": "",
      "min_premium": 1.0,
      "min_volume": 1000,
      "max_items": 10
    }
  }
"""

import datetime
import json
import logging
import os
import time
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).parent.absolute()
LOG_FILE = SCRIPT_DIR / "lof_arbitrage_push.log"
JISILU_BASE_URL = "https://www.jisilu.cn"
PROJECT_URL = "http://8.134.134.156/happy-lof/"
LEGACY_ENV_FILE = Path("/www/wwwroot/happy-lof/.env")

ENDPOINTS = (
    ("指数LOF", "/data/lof/index_lof_list/", "https://www.jisilu.cn/data/lof/", {}, True),
    ("股票LOF", "/data/lof/stock_lof_list/", "https://www.jisilu.cn/data/lof/", {}, True),
    ("QDII LOF", "/data/qdii/qdii_list/E", "https://www.jisilu.cn/data/qdii/", {"only_lof": "y"}, False),
    ("商品QDII", "/data/qdii/qdii_list/C", "https://www.jisilu.cn/data/qdii/", {"only_lof": "y"}, False),
)

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


def load_env_value(env_file, key):
    if not env_file.exists():
        return ""

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == key:
                    return value.strip().strip("\"'")
    except Exception as exc:
        logging.warning("读取环境变量文件失败 %s: %s", env_file, exc)
    return ""


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


def parse_percentage(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        clean_value = str(value).replace("%", "").replace(" ", "").strip()
        if clean_value in ("", "-", "--"):
            return 0.0
        return float(clean_value)
    except Exception:
        return 0.0


def has_value(value):
    if value is None:
        return False
    clean_value = str(value).replace("%", "").replace(",", "").strip()
    return clean_value not in ("", "-", "--")


def compute_premium(cell, price, api_premium_raw, prefer_estimate):
    if has_value(api_premium_raw):
        return parse_percentage(api_premium_raw), "接口"

    estimate = parse_float(cell.get("estimate_value"))
    fund_nav = parse_float(cell.get("fund_nav"))
    candidates = (
        (("估值", estimate), ("净值", fund_nav))
        if prefer_estimate
        else (("净值", fund_nav), ("估值", estimate))
    )

    if price > 0:
        for label, ref_value in candidates:
            if ref_value > 0:
                return (price / ref_value - 1) * 100, label

    return 0.0, "无"


def format_money_wan(value):
    if value >= 10000:
        return "%.2f亿" % (value / 10000)
    return "%.0f万" % value


class LofArbitragePush:
    def __init__(self, config):
        lof_config = config.get("lof", {})
        self.bark_url = (
            lof_config.get("bark_url")
            or config.get("newbond", {}).get("bark_url")
            or ""
        ).rstrip("/")
        self.jisilu_cookie = (
            lof_config.get("jisilu_cookie")
            or os.environ.get("JISILU_COOKIE", "")
            or load_env_value(LEGACY_ENV_FILE, "JISILU_COOKIE")
        )
        self.min_premium = float(lof_config.get("min_premium", 1.0))
        self.min_volume = float(lof_config.get("min_volume", 1000))
        self.max_items = int(lof_config.get("max_items", 10))
        self.auth_warning = ""

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        })
        if self.jisilu_cookie:
            self.session.headers.update({"Cookie": self.jisilu_cookie})

    def make_request(self, endpoint, referer, extra_params):
        url = JISILU_BASE_URL + endpoint
        params = {
            "___jsl": "LST___t=%d" % int(time.time() * 1000),
            "rp": "500",
            "page": "1",
        }
        params.update(extra_params or {})

        try:
            self.session.headers["Referer"] = referer
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logging.error("请求集思录失败 %s: %s", endpoint, exc)
            return {"rows": []}

    def parse_rows(self, data, fund_type, prefer_estimate):
        result = []
        for row in data.get("rows", []):
            cell = row.get("cell", {})
            try:
                price = parse_float(cell.get("price"))
                estimate_value = parse_float(cell.get("estimate_value"))
                fund_nav = parse_float(cell.get("fund_nav"))
                api_premium_raw = cell.get("discount_rt")
                if not prefer_estimate and not has_value(api_premium_raw):
                    api_premium_raw = cell.get("t1_premium_rate")

                premium_rate, premium_source = compute_premium(
                    cell, price, api_premium_raw, prefer_estimate
                )
                result.append({
                    "fund_id": cell.get("fund_id", ""),
                    "fund_name": cell.get("fund_nm", ""),
                    "price": price,
                    "change_pct": parse_percentage(cell.get("increase_rt")),
                    "net_value": fund_nav or estimate_value,
                    "premium_rate": premium_rate,
                    "volume": parse_float(cell.get("volume")),
                    "apply_status": cell.get("apply_status", ""),
                    "fund_type": fund_type,
                    "premium_source": premium_source,
                })
            except Exception as exc:
                logging.warning("解析 LOF 行失败: %s", exc)
        return result

    def get_all_lof(self):
        all_data = []
        category_counts = []
        suspect_categories = []

        for fund_type, endpoint, referer, params, prefer_estimate in ENDPOINTS:
            data = self.make_request(endpoint, referer, params)
            rows = data.get("rows", [])
            row_count = len(rows)
            category_counts.append("%s=%d" % (fund_type, row_count))
            if row_count == 20:
                suspect_categories.append(fund_type)
            all_data.extend(self.parse_rows(data, fund_type, prefer_estimate))

        if not self.jisilu_cookie:
            self.auth_warning = "未配置 JISILU_COOKIE，可能只能获取游客数据。"
            logging.warning(self.auth_warning)
        elif suspect_categories:
            self.auth_warning = (
                "疑似集思录 Cookie 失效：%s 分类只返回 20 条，游客态通常只显示前 20 条。"
                % "、".join(suspect_categories)
            )
            logging.warning("%s 分类数量：%s", self.auth_warning, "，".join(category_counts))
        else:
            logging.info("已加载 JISILU_COOKIE，分类数量：%s", "，".join(category_counts))

        return all_data

    def filter_targets(self, all_data):
        targets = []
        for fund in all_data:
            if "限" not in fund["apply_status"]:
                continue
            if fund["premium_rate"] < self.min_premium:
                continue
            if fund["volume"] < self.min_volume:
                continue
            targets.append(fund)

        return sorted(targets, key=lambda item: item["premium_rate"], reverse=True)

    def build_message(self, targets):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        shown = targets[:self.max_items]
        lines = [
            "发现 %d 只 LOF 套利候选，筛选口径：限购 + 溢价>=%.2f%% + 成交额>=%.0f万"
            % (len(targets), self.min_premium, self.min_volume),
            "时间：%s" % now,
            "",
        ]

        for index, fund in enumerate(shown, 1):
            change_sign = "+" if fund["change_pct"] > 0 else ""
            lines.append(
                "%d. %s（%s）\n"
                "价格：%.3f（%s%.2f%%）｜净值：%.3f\n"
                "成交额：%s｜实时溢价率：%.2f%%｜申购限额：%s"
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
                    fund["apply_status"] or "未知",
                )
            )

        if len(targets) > len(shown):
            lines.append("")
            lines.append("还有 %d 只未展示，请打开今乐福查看。" % (len(targets) - len(shown)))

        return "\n".join(lines)

    def send_msg(self, content):
        if not self.bark_url:
            logging.error("未配置 Bark 推送地址，请在 config.json 中配置 lof.bark_url 或 newbond.bark_url")
            return False

        title = "LOF套利提醒"
        bark_url = "%s/%s/%s" % (
            self.bark_url,
            requests.utils.quote(title),
            requests.utils.quote(content),
        )
        params = {
            "url": PROJECT_URL,
            "automaticallyCopy": "1",
            "copy": content,
        }

        try:
            response = self.session.get(bark_url, params=params, timeout=15)
            if response.status_code != 200:
                logging.error("Bark 请求失败，状态码: %s", response.status_code)
                return False
            result = response.json()
            if result.get("code") == 200:
                logging.info("Bark 消息发送成功")
                return True
            logging.error("Bark 消息发送失败: %s", result)
            return False
        except Exception as exc:
            logging.error("发送 Bark 消息异常: %s", exc)
            return False

    def push_msg(self):
        logging.info("开始检查 LOF 套利机会")
        all_data = self.get_all_lof()
        logging.info("获取 LOF 数据 %d 条", len(all_data))

        targets = self.filter_targets(all_data)
        if not targets:
            if self.auth_warning:
                content = "%s\n\n当前未发现符合条件的 LOF 套利机会。" % self.auth_warning
                logging.warning("发送 LOF 数据源告警:\n%s", content)
                self.send_msg(content)
            else:
                logging.info("暂无符合条件的 LOF 套利机会，不发送消息")
            return

        content = self.build_message(targets)
        if self.auth_warning:
            content = "%s\n\n%s" % (self.auth_warning, content)
        logging.info("发现 LOF 套利候选:\n%s", content)
        self.send_msg(content)


def main():
    logging.info("=" * 50)
    logging.info("LOF 基金套利提醒任务开始")
    config = load_config()
    LofArbitragePush(config).push_msg()
    logging.info("=" * 50)


if __name__ == "__main__":
    main()
