#!/bin/bash
# LOF 基金套利监控系统 - 生产环境启动脚本

# 设置环境变量
export PORT=5000
export DEBUG=False

# 启动应用
echo "正在启动 LOF 基金套利监控系统..."
python3 app.py
