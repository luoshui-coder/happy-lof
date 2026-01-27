#!/bin/bash

# 今乐福小程序发布 - 服务器检查脚本
# 用于验证服务器配置是否正确

echo "=========================================="
echo "今乐福小程序发布 - 服务器检查"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASS=0
FAIL=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. 检查 HTTPS 是否配置..."
if curl -s -o /dev/null -w "%{http_code}" https://luoshui.life | grep -q "200\|301\|302"; then
    check_pass "HTTPS 可访问"
else
    check_fail "HTTPS 无法访问，请先配置 SSL 证书"
fi

echo ""
echo "2. 检查 API 接口..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://luoshui.life/api/lof)
if [ "$HTTP_CODE" = "200" ]; then
    check_pass "API 接口正常 (HTTP $HTTP_CODE)"
else
    check_fail "API 接口异常 (HTTP $HTTP_CODE)"
fi

echo ""
echo "3. 检查 Flask 服务..."
if pgrep -f "python.*app.py" > /dev/null; then
    check_pass "Flask 服务正在运行"
    ps aux | grep "python.*app.py" | grep -v grep
else
    check_fail "Flask 服务未运行"
fi

echo ""
echo "4. 检查端口占用..."
if netstat -tlnp 2>/dev/null | grep -q ":5000"; then
    check_pass "5000 端口正在监听"
else
    check_fail "5000 端口未监听"
fi

echo ""
echo "5. 检查 Nginx 状态..."
if systemctl is-active --quiet nginx; then
    check_pass "Nginx 服务正在运行"
else
    check_warn "Nginx 服务未运行（如果使用宝塔面板可忽略）"
fi

echo ""
echo "6. 检查 SSL 证书..."
if [ -f "/etc/letsencrypt/live/luoshui.life/fullchain.pem" ]; then
    check_pass "SSL 证书文件存在"
    # 检查证书有效期
    EXPIRY=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/luoshui.life/fullchain.pem 2>/dev/null | cut -d= -f2)
    if [ -n "$EXPIRY" ]; then
        echo "   证书有效期至: $EXPIRY"
    fi
else
    check_warn "未找到 Let's Encrypt 证书（可能使用其他证书或宝塔面板）"
fi

echo ""
echo "7. 测试 API 响应内容..."
RESPONSE=$(curl -s https://luoshui.life/api/lof)
if echo "$RESPONSE" | grep -q "success"; then
    check_pass "API 返回正确的 JSON 数据"
    echo "   数据示例: $(echo $RESPONSE | head -c 100)..."
else
    check_fail "API 返回数据异常"
    echo "   响应内容: $RESPONSE"
fi

echo ""
echo "8. 检查数据库..."
if [ -f "lof_data.db" ]; then
    check_pass "数据库文件存在"
    DB_SIZE=$(du -h lof_data.db | cut -f1)
    echo "   数据库大小: $DB_SIZE"
else
    check_warn "数据库文件不存在（首次运行会自动创建）"
fi

echo ""
echo "=========================================="
echo "检查结果汇总"
echo "=========================================="
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！可以开始发布小程序${NC}"
    echo ""
    echo "下一步操作："
    echo "1. 登录微信公众平台配置域名白名单"
    echo "2. 使用微信开发者工具上传代码"
    echo "3. 提交审核"
else
    echo -e "${RED}✗ 存在 $FAIL 个问题，请先解决后再发布${NC}"
    echo ""
    echo "常见问题解决方案："
    echo "1. HTTPS 配置：使用宝塔面板申请 Let's Encrypt 证书"
    echo "2. Flask 服务：cd /path/to/project && python3 app.py"
    echo "3. Nginx 配置：检查反向代理配置是否正确"
fi

echo ""
echo "详细文档："
echo "- 小程序发布清单.md"
echo "- 小程序发布指南.md"
echo ""
