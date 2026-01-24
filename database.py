#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块 - 存储LOF历史溢价率数据
"""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
import os


class LOFDatabase:
    """LOF历史数据数据库"""
    
    def __init__(self, db_path: str = "lof_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建历史溢价率表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_id TEXT NOT NULL,
                fund_name TEXT NOT NULL,
                premium_rate REAL NOT NULL,
                price REAL NOT NULL,
                net_value REAL NOT NULL,
                volume REAL NOT NULL,
                record_date DATE NOT NULL,
                record_time DATETIME NOT NULL,
                UNIQUE(fund_id, record_date)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fund_date 
            ON premium_history(fund_id, record_date DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_daily_data(self, funds: List[Dict]) -> int:
        """保存当日数据（如果当天已存在则更新）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = date.today()
        now = datetime.now()
        count = 0
        
        for fund in funds:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO premium_history 
                    (fund_id, fund_name, premium_rate, price, net_value, volume, record_date, record_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fund['fund_id'],
                    fund['fund_name'],
                    fund['premium_rate'],
                    fund['price'],
                    fund['net_value'],
                    fund['volume'],
                    today,
                    now
                ))
                count += 1
            except Exception as e:
                print(f"保存数据失败 {fund['fund_id']}: {e}")
        
        conn.commit()
        conn.close()
        return count
    
    def get_history(self, fund_id: str, days: int = 30) -> List[Dict]:
        """获取指定基金的历史数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT record_date, premium_rate, price, net_value, volume
            FROM premium_history
            WHERE fund_id = ?
            ORDER BY record_date DESC
            LIMIT ?
        ''', (fund_id, days))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表（倒序，从旧到新）
        history = []
        for row in reversed(rows):
            history.append({
                'date': row[0],
                'premium_rate': row[1],
                'price': row[2],
                'net_value': row[3],
                'volume': row[4]
            })
        
        return history
    
    def get_latest_record_date(self) -> Optional[date]:
        """获取最新记录日期"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(record_date) FROM premium_history')
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return datetime.strptime(result[0], '%Y-%m-%d').date()
        return None
    
    def should_record_today(self) -> bool:
        """判断今天是否需要记录数据"""
        latest = self.get_latest_record_date()
        today = date.today()
        
        # 如果没有记录或最新记录不是今天，则需要记录
        return latest is None or latest < today


if __name__ == '__main__':
    # 测试
    db = LOFDatabase()
    print(f"数据库初始化完成: {db.db_path}")
    print(f"是否需要记录今日数据: {db.should_record_today()}")
