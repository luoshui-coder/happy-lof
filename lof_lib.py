
# -*- coding: utf-8 -*-
"""
LOF 基金套利核心逻辑库
包含数据获取 API 和数据模型
"""

import os
import requests
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


class JisiluAPI:
    """集思录 API 封装类"""
    
    BASE_URL = "https://www.jisilu.cn"
    # 经验阈值：正常登录态下 index_lof 行数通常远高于游客态
    GUEST_INDEX_THRESHOLD = 80
    
    ENDPOINTS = {
        "index_lof": "/data/lof/index_lof_list/",
        "stock_lof": "/data/lof/stock_lof_list/",
        "qdii_lof": "/data/qdii/qdii_list/E",
        "qdii_commodity": "/data/qdii/qdii_list/C",  # 商品型QDII（原油、黄金等）
    }
    
    def __init__(self, cookie: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        })
        
        # 优先使用传入的 cookie，否则尝试从环境变量读取
        self.cookie = cookie or os.environ.get("JISILU_COOKIE")
        if self.cookie:
            self.session.headers.update({"Cookie": self.cookie})

        # 鉴权状态缓存（用于 API 返回给前端）
        self.auth_status = {
            "status": "unknown",  # ok | suspect_guest | no_cookie | unknown
            "message": "尚未检测",
            "checked_at": None,
            "index_rows": None,
        }

    def _get_timestamp(self) -> str:
        return f"LST___t={int(time.time() * 1000)}"

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
            response = self.session.get(url, params=request_params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return {"rows": []}

    def _check_auth_status(self, index_rows: int) -> Dict[str, Any]:
        """根据指数LOF条数粗略判断是否退化到游客态"""
        checked_at = time.strftime("%Y-%m-%d %H:%M:%S")

        if not self.cookie:
            self.auth_status = {
                "status": "no_cookie",
                "message": "未配置 JISILU_COOKIE，可能仅能获取游客数据",
                "checked_at": checked_at,
                "index_rows": index_rows,
            }
        elif index_rows < self.GUEST_INDEX_THRESHOLD:
            self.auth_status = {
                "status": "suspect_guest",
                "message": f"疑似 cookie 失效（index_lof={index_rows} < {self.GUEST_INDEX_THRESHOLD}），建议更新 JISILU_COOKIE",
                "checked_at": checked_at,
                "index_rows": index_rows,
            }
            print(f"[AUTH] {self.auth_status['message']}")
        else:
            self.auth_status = {
                "status": "ok",
                "message": f"cookie 看起来有效（index_lof={index_rows}）",
                "checked_at": checked_at,
                "index_rows": index_rows,
            }

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

    def get_index_lof(self) -> List[LOFInfo]:
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
                net_value = self._parse_float(cell.get("fund_nav")) or self._parse_float(cell.get("estimate_value"))
                lof = LOFInfo(
                    fund_id=cell.get("fund_id", ""),
                    fund_name=cell.get("fund_nm", ""),
                    price=self._parse_float(cell.get("price")),
                    change_pct=self._parse_percentage(cell.get("increase_rt")),
                    net_value=net_value,
                    premium_rate=self._parse_percentage(cell.get("discount_rt")),
                    volume=self._parse_float(cell.get("volume")),
                    apply_status=cell.get("apply_status", ""),
                    fund_type=fund_type
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
                net_value = self._parse_float(cell.get("fund_nav")) or self._parse_float(cell.get("estimate_value"))
                premium = cell.get("discount_rt") or cell.get("t1_premium_rate")
                lof = LOFInfo(
                    fund_id=cell.get("fund_id", ""),
                    fund_name=cell.get("fund_nm", ""),
                    price=self._parse_float(cell.get("price")),
                    change_pct=self._parse_percentage(cell.get("increase_rt")),
                    net_value=net_value,
                    premium_rate=self._parse_percentage(premium),
                    volume=self._parse_float(cell.get("volume")),
                    apply_status=cell.get("apply_status", ""),
                    fund_type=fund_type
                )
                result.append(lof)
            except Exception as e:
                print(f"解析 QDII 失败: {e}")
        return result

    def get_all_lof(self) -> List[LOFInfo]:
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
