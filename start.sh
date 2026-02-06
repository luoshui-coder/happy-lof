#!/bin/bash
# 今乐福启动脚本

echo "正在启动今乐福服务..."
cd "$(dirname "$0")"

# 检查 venv 是否存在，不存在则创建
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 检查依赖
echo "检查依赖..."
./venv/bin/pip install -r requirements.txt

# 启动服务
echo "启动端口: $(grep PORT .env | cut -d '=' -f2)"
./venv/bin/python app.py
