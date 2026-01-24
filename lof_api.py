#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOF 基金套利数据接口 Demo
从集思录获取 LOF 基金溢价数据，用于套利参考

数据来源：https://www.jisilu.cn/
"""

import requests
import time
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LOFInfo:
    """LOF 基金信息"""
    fund_id: str        # 基金代码
    fund_name: str      # 基金名称
    price: float        # 当前价格
    change_pct: float   # 涨跌幅 (%)
    net_value: float    # 净值
    premium_rate: float # 溢价率 (%)
    volume: float       # 成交额 (万元)
    apply_status: str   # 申购状态
    fund_type: str      # 基金类型 (指数LOF/股票LOF/QDII)


class JisiluAPI:
    """集思录 API 封装类"""
    
    BASE_URL = "https://www.jisilu.cn"
    
    # API 端点
    ENDPOINTS = {
        "index_lof": "/data/lof/index_lof_list/",
        "stock_lof": "/data/lof/stock_lof_list/",
        "qdii_lof": "/data/qdii/qdii_list/E",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        })

    def _get_timestamp(self) -> str:
        """生成时间戳参数"""
        return f"LST___t={int(time.time() * 1000)}"

    def _make_request(self, endpoint: str, referer: str, params: Optional[Dict] = None) -> Dict:
        """发起 API 请求"""
        url = f"{self.BASE_URL}{endpoint}"
        
        # 更新 Referer
        self.session.headers["Referer"] = referer
        
        # 构建参数
        request_params = {
            "___jsl": self._get_timestamp(),
            "rp": "100",  # 每页100条
            "page": "1",
        }
        if params:
            request_params.update(params)
        
        try:
            response = self.session.get(url, params=request_params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"rows": []}
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            return {"rows": []}

    def _parse_percentage(self, value: Any) -> float:
        """解析百分比字符串为浮点数"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # 移除百分号和空格
            clean_value = str(value).replace("%", "").replace(" ", "").strip()
            if clean_value in ("", "-", "--"):
                return 0.0
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    def _parse_float(self, value: Any) -> float:
        """安全解析浮点数"""
        if value is None:
            return 0.0
        try:
            clean_value = str(value).replace(",", "").strip()
            if clean_value in ("", "-", "--"):
                return 0.0
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    def get_index_lof(self) -> List[LOFInfo]:
        """获取指数 LOF 数据"""
        data = self._make_request(
            self.ENDPOINTS["index_lof"],
            referer=f"{self.BASE_URL}/data/lof/"
        )
        return self._parse_lof_data(data, "指数LOF")

    def get_stock_lof(self) -> List[LOFInfo]:
        """获取股票 LOF 数据"""
        data = self._make_request(
            self.ENDPOINTS["stock_lof"],
            referer=f"{self.BASE_URL}/data/lof/"
        )
        return self._parse_lof_data(data, "股票LOF")

    def get_qdii_lof(self) -> List[LOFInfo]:
        """获取 QDII LOF 数据"""
        data = self._make_request(
            self.ENDPOINTS["qdii_lof"],
            referer=f"{self.BASE_URL}/data/qdii/",
            params={"only_lof": "y"}  # 仅显示 LOF
        )
        return self._parse_qdii_data(data)

    def _parse_lof_data(self, data: Dict, fund_type: str) -> List[LOFInfo]:
        """解析 LOF 数据"""
        result = []
        rows = data.get("rows", [])
        
        for row in rows:
            cell = row.get("cell", {})
            try:
                # 净值优先使用 fund_nav，其次 estimate_value
                net_value = self._parse_float(cell.get("fund_nav")) or self._parse_float(cell.get("estimate_value"))
                
                lof = LOFInfo(
                    fund_id=cell.get("fund_id", ""),
                    fund_name=cell.get("fund_nm", ""),
                    price=self._parse_float(cell.get("price")),
                    change_pct=self._parse_percentage(cell.get("increase_rt")),
                    net_value=net_value,
                    premium_rate=self._parse_percentage(cell.get("discount_rt")),
                    volume=self._parse_float(cell.get("volume")),
                    apply_status=cell.get("apply_status", cell.get("apply_cd", "")),
                    fund_type=fund_type
                )
                result.append(lof)
            except Exception as e:
                print(f"解析数据失败: {e}, cell: {cell}")
        
        return result

    def _parse_qdii_data(self, data: Dict) -> List[LOFInfo]:
        """解析 QDII 数据（字段略有不同）"""
        result = []
        rows = data.get("rows", [])
        
        for row in rows:
            cell = row.get("cell", {})
            try:
                # 净值优先使用 fund_nav，其次 estimate_value
                net_value = self._parse_float(cell.get("fund_nav")) or self._parse_float(cell.get("estimate_value"))
                # QDII 的溢价率字段可能带有百分号
                premium = cell.get("discount_rt") or cell.get("t1_premium_rate")
                
                lof = LOFInfo(
                    fund_id=cell.get("fund_id", ""),
                    fund_name=cell.get("fund_nm", ""),
                    price=self._parse_float(cell.get("price")),
                    change_pct=self._parse_percentage(cell.get("increase_rt")),
                    net_value=net_value,
                    premium_rate=self._parse_percentage(premium),
                    volume=self._parse_float(cell.get("volume")),
                    apply_status=cell.get("apply_status", cell.get("apply_cd", "")),
                    fund_type="QDII"
                )
                result.append(lof)
            except Exception as e:
                print(f"解析 QDII 数据失败: {e}, cell: {cell}")
        
        return result

    def get_all_lof(self) -> List[LOFInfo]:
        """获取全部 LOF 数据（指数 LOF + QDII LOF）"""
        all_data = []
        
        print("正在获取指数 LOF...")
        all_data.extend(self.get_index_lof())
        
        print("正在获取 QDII LOF...")
        all_data.extend(self.get_qdii_lof())
        
        return all_data


def filter_lof(
    data: List[LOFInfo],
    min_premium: float = 0.0,
    min_volume: float = 0.0,
    only_limited: bool = False,
    sort_by_premium: bool = True
) -> List[LOFInfo]:
    """
    筛选 LOF 基金
    
    Args:
        data: LOF 数据列表
        min_premium: 最低溢价率阈值 (%)
        min_volume: 最低成交额阈值 (万元)
        only_limited: 仅显示限购/暂停申购的
        sort_by_premium: 按溢价率降序排序
    
    Returns:
        筛选后的 LOF 列表
    """
    filtered = data
    
    # 按溢价率筛选
    if min_premium > 0:
        filtered = [lof for lof in filtered if lof.premium_rate >= min_premium]
    
    # 按成交额筛选
    if min_volume > 0:
        filtered = [lof for lof in filtered if lof.volume >= min_volume]
    
    # 按申购状态筛选
    if only_limited:
        filtered = [lof for lof in filtered if lof.apply_status not in ("开放申购", "开放", "")]
    
    # 排序
    if sort_by_premium:
        filtered = sorted(filtered, key=lambda x: x.premium_rate, reverse=True)
    
    return filtered


def format_output(data: List[LOFInfo], top_n: int = 20) -> str:
    """
    格式化输出（类似华宝证券截图）
    
    Args:
        data: LOF 数据列表
        top_n: 显示前 N 条
    
    Returns:
        格式化的字符串
    """
    lines = []
    lines.append("=" * 80)
    lines.append("                        LOF 溢价表")
    lines.append("=" * 80)
    lines.append(f"{'标的':<20} {'价格':>8} {'涨跌':>8} {'净值':>8} {'溢价率':>8} {'成交额':>10} {'类型'}")
    lines.append("-" * 80)
    
    for lof in data[:top_n]:
        name_code = f"{lof.fund_name[:8]}({lof.fund_id})"
        change_str = f"{lof.change_pct:+.2f}%" if lof.change_pct != 0 else "-"
        premium_str = f"{lof.premium_rate:.2f}%"
        volume_str = f"{lof.volume:.0f}万" if lof.volume < 10000 else f"{lof.volume/10000:.2f}亿"
        
        lines.append(
            f"{name_code:<18} {lof.price:>8.3f} {change_str:>8} "
            f"{lof.net_value:>8.3f} {premium_str:>8} {volume_str:>10} {lof.fund_type}"
        )
    
    lines.append("-" * 80)
    lines.append(f"共 {len(data)} 只基金，显示前 {min(top_n, len(data))} 只")
    
    return "\n".join(lines)


def export_json(data: List[LOFInfo], filepath: str = "lof_data.json"):
    """导出为 JSON 格式（供小程序使用）"""
    export_data = [
        {
            "fund_id": lof.fund_id,
            "fund_name": lof.fund_name,
            "price": lof.price,
            "change_pct": lof.change_pct,
            "net_value": lof.net_value,
            "premium_rate": lof.premium_rate,
            "volume": lof.volume,
            "apply_status": lof.apply_status,
            "fund_type": lof.fund_type
        }
        for lof in data
    ]
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已导出到: {filepath}")


def main():
    """主函数"""
    print("=" * 50)
    print("LOF 基金套利数据接口 Demo")
    print("=" * 50)
    print()
    
    # 初始化 API
    api = JisiluAPI()
    
    # 获取全部数据
    all_lof = api.get_all_lof()
    print(f"\n共获取 {len(all_lof)} 只 LOF 基金数据")
    
    # 筛选高溢价基金（溢价率 > 1%，成交额 >= 1000万，且排除开放申购）
    high_premium = filter_lof(all_lof, min_premium=1.0, min_volume=1000, only_limited=True, sort_by_premium=True)
    
    print("\n" + "=" * 50)
    print("高溢价 LOF 基金 (溢价率 > 1%)")
    print("=" * 50 + "\n")
    print(format_output(high_premium, top_n=30))
    
    # 导出 JSON
    export_json(high_premium, "lof_high_premium.json")
    export_json(all_lof, "lof_all.json")
    
    print("\n完成！")


if __name__ == "__main__":
    main()
