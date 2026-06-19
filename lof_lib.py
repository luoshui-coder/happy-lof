
# -*- coding: utf-8 -*-
"""
LOF 基金套利核心逻辑库
包含数据获取 API 和数据模型
"""

import os
import re
import requests
import threading
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class LOFInfo:
    """LOF 基金信息"""
    fund_id: str
    fund_name: str
    price: float
    change_pct: float
    net_value: float
    premium_rate: float
    volume: float
    apply_status: str
    fund_type: str
    estimate_value: float = 0.0
    nav_date: str = ""
    premium_source: str = ""  # "接口" | "估值" | "净值" | "无"


class JisiluAPI:
    """集思录 API 封装类"""
    
    BASE_URL = "https://www.jisilu.cn"
    # 经验阈值：正常登录态下 index_lof 行数通常远高于游客态
    GUEST_INDEX_THRESHOLD = 80
    LOGIN_PAGE = "/login/"
    LOGIN_ENDPOINT = "/webapi/account/login_process/"
    LOGIN_KEY_RE = re.compile(r"var\s+key\s*=\s*'([^']+)'")
    _cookie_cache_lock = threading.Lock()
    _cookie_cache: Dict[str, Any] = {
        "username": "",
        "cookie": "",
        "expires_at": 0.0,
    }
    
    ENDPOINTS = {
        "index_lof": "/data/lof/index_lof_list/",
        "stock_lof": "/data/lof/stock_lof_list/",
        "qdii_lof": "/data/qdii/qdii_list/E",
        "qdii_commodity": "/data/qdii/qdii_list/C",  # 商品型QDII（原油、黄金等）
    }
    
    def __init__(
        self,
        cookie: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 10,
    ):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        })
        
        # 优先使用动态登录凭据，静态 Cookie 作为兜底。
        self.cookie = cookie or os.environ.get("JISILU_COOKIE", "")
        self.username = username or os.environ.get("JISILU_USERNAME", "")
        self.password = password or os.environ.get("JISILU_PASSWORD", "")
        self.cookie_cache_ttl = self._parse_int(os.environ.get("JISILU_COOKIE_CACHE_TTL")) or 3600
        self.timeout = timeout
        self.auth_source = "static_cookie" if self.cookie else "none"
        self.login_message = ""
        self._login_attempted = False
        if self.cookie:
            self._set_cookie_header(self.cookie)

        # 鉴权状态缓存（用于 API 返回给前端）
        self.auth_status = {
            "status": "unknown",  # ok | suspect_guest | no_cookie | error | unknown
            "message": "尚未检测",
            "checked_at": None,
            "index_rows": None,
            "has_cookie": self.has_auth_cookie(),
            "auth_source": self.auth_source,
            "login_message": self.login_message,
        }

    def _get_timestamp(self) -> str:
        return f"LST___t={int(time.time() * 1000)}"

    def _parse_int(self, value: Any) -> Optional[int]:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    def _set_cookie_header(self, cookie: str) -> None:
        self.cookie = cookie or ""
        if self.cookie:
            self.session.headers.update({"Cookie": self.cookie})
        else:
            self.session.headers.pop("Cookie", None)

    def _session_cookie_header(self) -> str:
        return "; ".join(
            f"{cookie.name}={cookie.value}"
            for cookie in self.session.cookies
            if cookie.value is not None
        )

    def has_auth_cookie(self) -> bool:
        return bool(self.cookie or self._session_cookie_header())

    def can_dynamic_login(self) -> bool:
        return bool(self.username and self.password)

    @staticmethod
    def _jslencode(text: str, aes_key: str) -> str:
        try:
            import pyaes
        except ImportError as exc:
            raise RuntimeError("缺少 pyaes 依赖，无法执行集思录动态登录") from exc

        key = aes_key.encode("utf-8")
        if len(key) != 16:
            raise RuntimeError("集思录登录 AES key 长度异常")

        raw = str(text).encode("utf-8")
        pad_len = 16 - (len(raw) % 16)
        raw += bytes([pad_len]) * pad_len
        aes = pyaes.AESModeOfOperationECB(key)
        encrypted = b"".join(aes.encrypt(raw[i:i + 16]) for i in range(0, len(raw), 16))
        return encrypted.hex()

    def _cached_cookie(self) -> str:
        if not self.username:
            return ""
        now = time.time()
        with self._cookie_cache_lock:
            if (
                self._cookie_cache.get("username") == self.username
                and self._cookie_cache.get("cookie")
                and float(self._cookie_cache.get("expires_at") or 0) > now
            ):
                return str(self._cookie_cache["cookie"])
        return ""

    def _store_cached_cookie(self, cookie: str) -> None:
        if not self.username or not cookie:
            return
        with self._cookie_cache_lock:
            self._cookie_cache.update({
                "username": self.username,
                "cookie": cookie,
                "expires_at": time.time() + max(int(self.cookie_cache_ttl), 60),
            })

    def login(self) -> bool:
        if not self.can_dynamic_login():
            self.login_message = "未配置 JISILU_USERNAME/JISILU_PASSWORD，无法动态登录"
            return False

        cached_cookie = self._cached_cookie()
        if cached_cookie:
            self._set_cookie_header(cached_cookie)
            self.auth_source = "dynamic_cache"
            self.login_message = "已复用动态登录 Cookie 缓存"
            return True

        previous_cookie = self.cookie
        previous_auth_source = self.auth_source
        self.session.headers.pop("Cookie", None)
        self.session.cookies.clear()

        login_page_url = f"{self.BASE_URL}{self.LOGIN_PAGE}"
        response = self.session.get(
            login_page_url,
            headers={"Referer": self.BASE_URL},
            timeout=self.timeout,
        )
        response.raise_for_status()
        match = self.LOGIN_KEY_RE.search(response.text)
        if not match:
            self._set_cookie_header(previous_cookie)
            self.auth_source = previous_auth_source
            self.login_message = "集思录登录页未找到 AES key"
            return False

        aes_key = match.group(1)
        data = {
            "return_url": f"{self.BASE_URL}/data/lof/",
            "user_name": self._jslencode(self.username, aes_key),
            "password": self._jslencode(self.password, aes_key),
            "aes": "1",
            "auto_login": "1",
        }
        login_response = self.session.post(
            f"{self.BASE_URL}{self.LOGIN_ENDPOINT}",
            data=data,
            headers={"Referer": login_page_url},
            timeout=self.timeout,
        )
        login_response.raise_for_status()
        payload = login_response.json()
        if payload.get("code") != 200:
            captcha = bool((payload.get("data") or {}).get("captcha"))
            suffix = "；需要验证码，已降级使用现有 Cookie/游客态" if captcha else ""
            self._set_cookie_header(previous_cookie)
            self.auth_source = previous_auth_source
            self.login_message = f"动态登录失败：{payload.get('msg') or '未知错误'}{suffix}"
            return False

        cookie = self._session_cookie_header()
        if not cookie:
            self._set_cookie_header(previous_cookie)
            self.auth_source = previous_auth_source
            self.login_message = "动态登录成功但未获取到 Cookie"
            return False

        self._set_cookie_header(cookie)
        self._store_cached_cookie(cookie)
        self.auth_source = "dynamic_login"
        self.login_message = "动态登录成功"
        return True

    def _ensure_dynamic_cookie(self) -> None:
        if self.has_auth_cookie() or not self.can_dynamic_login() or self._login_attempted:
            return
        self._login_attempted = True
        try:
            self.login()
        except Exception as exc:
            if self.cookie:
                self._set_cookie_header(self.cookie)
            self.login_message = f"动态登录异常：{exc}"

    def _make_request(self, endpoint: str, referer: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.BASE_URL}{endpoint}"
        self.session.headers["Referer"] = referer
        
        request_params = {
            "___jsl": self._get_timestamp(),
            "rp": "500",
            "page": "1",
        }
        if params:
            request_params.update(params)
        
        try:
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return {"rows": []}

    def _check_auth_status(self, index_rows: int) -> Dict[str, Any]:
        """根据指数LOF条数粗略判断是否退化到游客态"""
        checked_at = time.strftime("%Y-%m-%d %H:%M:%S")

        has_cookie = self.has_auth_cookie()
        base = {
            "checked_at": checked_at,
            "index_rows": index_rows,
            "has_cookie": has_cookie,
            "auth_source": self.auth_source,
            "login_message": self.login_message,
        }

        if not has_cookie:
            self.auth_status = {
                "status": "no_cookie",
                "message": "未配置可用的集思录 Cookie，可能仅能获取游客数据",
                **base,
            }
        elif index_rows < self.GUEST_INDEX_THRESHOLD:
            self.auth_status = {
                "status": "suspect_guest",
                "message": f"疑似 cookie 失效或权限不足（index_lof={index_rows} < {self.GUEST_INDEX_THRESHOLD}）",
                **base,
            }
            print(f"[AUTH] {self.auth_status['message']}")
        else:
            self.auth_status = {
                "status": "ok",
                "message": f"cookie 看起来有效（index_lof={index_rows}）",
                **base,
            }

        if self.login_message and self.login_message not in self.auth_status["message"]:
            self.auth_status["message"] = f"{self.auth_status['message']}；{self.login_message}"

        return self.auth_status

    def get_auth_status(self) -> Dict[str, Any]:
        return self.auth_status

    def _parse_percentage(self, value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            clean_value = str(value).replace("%", "").replace(" ", "").strip()
            if clean_value in ("", "-", "--"):
                return 0.0
            return float(clean_value)
        except:
            return 0.0

    def _parse_float(self, value: Any) -> float:
        if value is None:
            return 0.0
        try:
            clean_value = str(value).replace(",", "").strip()
            if clean_value in ("", "-", "--"):
                return 0.0
            return float(clean_value)
        except:
            return 0.0

    def _has_value(self, raw: Any) -> bool:
        """原始字段是否确实有值（区分'字段被屏蔽'与'确为 0'）"""
        if raw is None:
            return False
        s = str(raw).replace("%", "").replace(",", "").strip()
        return s not in ("", "-", "--")

    def _compute_premium(
        self,
        cell: Dict,
        price: float,
        api_premium_raw: Any,
        prefer_estimate: bool,
    ) -> (float, str):
        """
        计算溢价率，返回 (premium_rate, source_label)。

        优先级：
        1. 接口自带溢价率非空 -> 直接使用（后向兼容集思录字段恢复）
        2. 按 prefer_estimate 顺序挑参考净值并用 price 自算
        3. 都不可用 -> (0.0, "无")
        """
        if self._has_value(api_premium_raw):
            return self._parse_percentage(api_premium_raw), "接口"

        estimate = self._parse_float(cell.get("estimate_value"))
        fund_nav = self._parse_float(cell.get("fund_nav"))

        candidates = (
            [("估值", estimate), ("净值", fund_nav)]
            if prefer_estimate
            else [("净值", fund_nav), ("估值", estimate)]
        )

        if price > 0:
            for label, ref in candidates:
                if ref > 0:
                    return (price / ref - 1) * 100, label

        return 0.0, "无"

    def get_index_lof(self) -> List[LOFInfo]:
        self._ensure_dynamic_cookie()
        data = self._make_request(
            self.ENDPOINTS["index_lof"],
            referer=f"{self.BASE_URL}/data/lof/"
        )
        rows = data.get("rows", [])
        self._check_auth_status(len(rows))
        return self._parse_lof_data(data, "指数LOF")

    def get_stock_lof(self) -> List[LOFInfo]:
        """获取股票型 LOF 数据"""
        data = self._make_request(
            self.ENDPOINTS["stock_lof"],
            referer=f"{self.BASE_URL}/data/lof/"
        )
        return self._parse_lof_data(data, "股票LOF")

    def get_qdii_lof(self) -> List[LOFInfo]:
        data = self._make_request(
            self.ENDPOINTS["qdii_lof"],
            referer=f"{self.BASE_URL}/data/qdii/",
            params={"only_lof": "y"}
        )
        return self._parse_qdii_data(data)

    def get_qdii_commodity(self) -> List[LOFInfo]:
        """获取 QDII 商品基金数据（原油、黄金等）"""
        data = self._make_request(
            self.ENDPOINTS["qdii_commodity"],
            referer=f"{self.BASE_URL}/data/qdii/",
            params={"only_lof": "y"}
        )
        return self._parse_qdii_data(data, fund_type="QDII")

    def _parse_lof_data(self, data: Dict, fund_type: str) -> List[LOFInfo]:
        result = []
        for row in data.get("rows", []):
            cell = row.get("cell", {})
            try:
                price = self._parse_float(cell.get("price"))
                estimate_value = self._parse_float(cell.get("estimate_value"))
                fund_nav = self._parse_float(cell.get("fund_nav"))
                net_value = fund_nav or estimate_value
                premium_rate, premium_source = self._compute_premium(
                    cell, price, cell.get("discount_rt"), prefer_estimate=True
                )
                lof = LOFInfo(
                    fund_id=cell.get("fund_id", ""),
                    fund_name=cell.get("fund_nm", ""),
                    price=price,
                    change_pct=self._parse_percentage(cell.get("increase_rt")),
                    net_value=net_value,
                    premium_rate=premium_rate,
                    volume=self._parse_float(cell.get("volume")),
                    apply_status=cell.get("apply_status", ""),
                    fund_type=fund_type,
                    estimate_value=estimate_value,
                    nav_date=cell.get("fund_nav_dt", "") or cell.get("nav_dt", ""),
                    premium_source=premium_source,
                )
                result.append(lof)
            except Exception as e:
                print(f"解析失败: {e}")
        return result

    def _parse_qdii_data(self, data: Dict, fund_type: str = "QDII") -> List[LOFInfo]:
        result = []
        for row in data.get("rows", []):
            cell = row.get("cell", {})
            try:
                price = self._parse_float(cell.get("price"))
                estimate_value = self._parse_float(cell.get("estimate_value"))
                fund_nav = self._parse_float(cell.get("fund_nav"))
                net_value = fund_nav or estimate_value
                # QDII 接口溢价率字段可能是 discount_rt 或 t1_premium_rate，取第一个有值的
                api_premium_raw = (
                    cell.get("discount_rt")
                    if self._has_value(cell.get("discount_rt"))
                    else cell.get("t1_premium_rate")
                )
                premium_rate, premium_source = self._compute_premium(
                    cell, price, api_premium_raw, prefer_estimate=False
                )
                lof = LOFInfo(
                    fund_id=cell.get("fund_id", ""),
                    fund_name=cell.get("fund_nm", ""),
                    price=price,
                    change_pct=self._parse_percentage(cell.get("increase_rt")),
                    net_value=net_value,
                    premium_rate=premium_rate,
                    volume=self._parse_float(cell.get("volume")),
                    apply_status=cell.get("apply_status", ""),
                    fund_type=fund_type,
                    estimate_value=estimate_value,
                    nav_date=cell.get("fund_nav_dt", "") or cell.get("nav_dt", ""),
                    premium_source=premium_source,
                )
                result.append(lof)
            except Exception as e:
                print(f"解析 QDII 失败: {e}")
        return result

    def get_all_lof(self) -> List[LOFInfo]:
        if not self.has_auth_cookie():
            self._ensure_dynamic_cookie()

        all_data = self._fetch_all_lof_once()
        if self.auth_status.get("status") == "ok" or not self.can_dynamic_login():
            return all_data

        try:
            logged_in = self.login()
        except Exception as exc:
            if self.cookie:
                self._set_cookie_header(self.cookie)
            self.login_message = f"动态登录异常：{exc}"
            logged_in = False

        if not logged_in:
            self.auth_status["login_message"] = self.login_message
            if self.login_message and self.login_message not in self.auth_status["message"]:
                self.auth_status["message"] = f"{self.auth_status['message']}；{self.login_message}"
            return all_data

        all_data = self._fetch_all_lof_once()
        self.auth_status["login_message"] = self.login_message
        return all_data

    def _fetch_all_lof_once(self) -> List[LOFInfo]:
        all_data = []
        all_data.extend(self.get_index_lof())
        all_data.extend(self.get_stock_lof())  # 新增
        all_data.extend(self.get_qdii_lof())
        all_data.extend(self.get_qdii_commodity())
        return all_data


def filter_lof(
    data: List[LOFInfo],
    min_premium: Optional[float] = None,
    min_volume: float = 0.0,
    only_limited: bool = False
) -> List[LOFInfo]:
    """筛选 LOF 基金"""
    filtered = data
    
    # 允许传入负数作为筛选门槛
    if min_premium is not None:
        filtered = [lof for lof in filtered if lof.premium_rate >= min_premium]
    
    if min_volume > 0:
        # 暂停或限购的基金即使成交额不足也保留（可能是停牌或核心套利标的）
        filtered = [lof for lof in filtered if lof.volume >= min_volume or "暂停" in lof.apply_status or "限" in lof.apply_status]
    
    if only_limited:
        filtered = [lof for lof in filtered if lof.apply_status not in ("开放申购", "开放", "")]
    
    # 按溢价率降序排序
    filtered = sorted(filtered, key=lambda x: x.premium_rate, reverse=True)
    
    return filtered
