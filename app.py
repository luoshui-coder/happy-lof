#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今乐福 - LOF 基金套利基金溢价查询
Flask 后端 API 服务
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import time
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv
from database import LOFDatabase
from scheduler import LOFScheduler
from lof_lib import LOFInfo, JisiluAPI, filter_lof

# 加载环境变量
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)  # 允许跨域

# 初始化数据库和定时任务
db = LOFDatabase()
scheduler = LOFScheduler()
scheduler.start()  # 启动定时任务


# API 实例
api = JisiluAPI()





@app.route('/happy-lof')
def index():
    """首页"""
    return send_from_directory('static', 'index.html')


@app.route('/api/lof')
def get_lof_data():
    """获取 LOF 套利数据 API"""
    try:
        all_lof = api.get_all_lof()
        # 筛选：溢价率 >= 1%，成交额 >= 1000万，非开放申购
        filtered = filter_lof(all_lof, min_premium=1.0, min_volume=1000, only_limited=True)
        
        return jsonify({
            "success": True,
            "data": [asdict(lof) for lof in filtered],
            "total": len(filtered),
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/lof/all')
def get_all_lof_data():
    """获取全部 LOF 数据 API"""
    try:
        all_lof = api.get_all_lof()
        # 只排除开放申购，按溢价率排序
        filtered = filter_lof(all_lof, only_limited=True)
        
        return jsonify({
            "success": True,
            "data": [asdict(lof) for lof in filtered],
            "total": len(filtered),
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/lof/history/<fund_id>')
def get_lof_history(fund_id):
    """获取指定基金的历史溢价率数据"""
    try:
        days = int(request.args.get('days', 30))
        history = db.get_history(fund_id, days)
        
        return jsonify({
            "success": True,
            "fund_id": fund_id,
            "data": history,
            "total": len(history)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    # 从环境变量读取配置，方便部署
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("=" * 50)
    print("今乐福 - LOF 基金套利溢价查询")
    print("=" * 50)
    print(f"访问 http://127.0.0.1:{port} 查看页面")
    print(f"API: http://127.0.0.1:{port}/api/lof")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    
    if os.environ.get('JISILU_COOKIE'):
        print("状态: 已检测到集思录 Cookie，将尝试获取完整数据")
    else:
        print("提示: 未检测到 JISILU_COOKIE 环境变量，可能仅显示前20条数据")
        print("      请设置 export JISILU_COOKIE='你的cookie' 后重启获取完整权限")
        
    print("=" * 50)
    
    app.run(debug=debug, host='0.0.0.0', port=port)