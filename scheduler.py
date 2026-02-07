#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模块 - 每天14:55自动记录溢价率数据
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import LOFDatabase
from lof_lib import JisiluAPI, filter_lof
from dotenv import load_dotenv

load_dotenv()


class LOFScheduler:
    """LOF数据定时记录器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = LOFDatabase()
        self.api = JisiluAPI()
    
    def record_daily_data(self):
        """记录当日数据"""
        try:
            print(f"[{datetime.now()}] 开始记录今日LOF数据...")
            
            # 获取所有LOF数据
            all_lof = self.api.get_all_lof()
            
            # 记录所有 LOF 数据（包括折价），以便查看完整历史
            # valid_lof = [lof for lof in all_lof if lof.premium_rate > 0]
            valid_lof = all_lof
            
            # 转换为字典
            lof_dicts = [lof.__dict__ for lof in valid_lof]
            
            # 保存到数据库
            count = self.db.save_daily_data(lof_dicts)
            
            print(f"[{datetime.now()}] 记录完成，共保存 {count} 条数据")
            
        except Exception as e:
            print(f"[{datetime.now()}] 记录失败: {e}")
    
    def start(self):
        """启动定时任务"""
        # 每天14:55执行
        self.scheduler.add_job(
            self.record_daily_data,
            'cron',
            hour=14,
            minute=55,
            id='daily_record'
        )
        
        self.scheduler.start()
        print("定时任务已启动：每天14:55自动记录LOF数据")
    
    def stop(self):
        """停止定时任务"""
        self.scheduler.shutdown()
        print("定时任务已停止")


if __name__ == '__main__':
    # 测试
    scheduler = LOFScheduler()
    
    # 立即执行一次（测试）
    print("立即执行一次记录...")
    scheduler.record_daily_data()
    
    # 启动定时任务
    # scheduler.start()
    
    # 保持运行
    # import time
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     scheduler.stop()
