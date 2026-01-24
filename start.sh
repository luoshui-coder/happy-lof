#!/bin/bash
# 今乐福启动脚本

echo "正在启动今乐福服务..."
cd "$(dirname "$0")"

# 检查依赖
if ! pip3 show flask-cors > /dev/null 2>&1; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 启动服务
python3 app.py
