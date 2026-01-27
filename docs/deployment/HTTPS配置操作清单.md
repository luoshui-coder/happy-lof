# HTTPS 证书申请操作清单

## 📝 操作步骤（按顺序执行）

### ✅ 第一步：检查安全组和防火墙

- [ ] **云服务商安全组**（阿里云/腾讯云控制台）
  - 开放端口：80、443、5000
  - 协议：TCP
  - 授权对象：0.0.0.0/0

- [ ] **宝塔面板安全设置**
  - 路径：宝塔面板 → 安全
  - 确认已放行：80、443、5000 端口

### ✅ 第二步：修改 Nginx 配置

1. **登录宝塔面板**
   - 进入：网站 → luoshui.life → 设置

2. **修改配置文件**
   - 点击：配置文件
   - 将 `listen 5000;` 改为 `listen 80;`
   - 或者直接使用 `nginx-config-fixed.conf` 的内容

3. **关键配置检查**
   ```nginx
   server {
       listen 80;  # ✅ 必须是 80
       server_name luoshui.life;
       
       # ✅ 必须有这个配置
       location /.well-known/ {
           root /www/wwwroot/java_node_ssl;
           allow all;
       }
       
       # ✅ 反向代理到你的应用
       location / {
           proxy_pass http://127.0.0.1:5000;
           ...
       }
   }
   ```

4. **保存并重启 Nginx**
   - 点击：保存
   - 宝塔面板会自动重启 Nginx

### ✅ 第三步：验证配置

在服务器 SSH 中执行：

```bash
# 1. 检查 Nginx 是否监听 80 端口
sudo netstat -tlnp | grep :80

# 应该看到类似输出：
# tcp  0  0  0.0.0.0:80  0.0.0.0:*  LISTEN  12345/nginx

# 2. 测试 HTTP 访问
curl -I http://luoshui.life

# 应该返回 200 或 301/302
```

### ✅ 第四步：申请 Let's Encrypt 证书

1. **进入 SSL 设置**
   - 宝塔面板 → 网站 → luoshui.life → SSL

2. **选择 Let's Encrypt**
   - 验证方式：文件验证（默认）
   - 勾选域名：luoshui.life

3. **点击申请**
   - 等待 30-60 秒
   - 如果成功，会显示证书信息

### ✅ 第五步：启用 HTTPS（证书申请成功后）

1. **修改配置文件**
   - 在 `nginx-config-fixed.conf` 中取消注释 HTTPS 部分（443 端口）
   - 或者在宝塔面板中勾选"强制 HTTPS"

2. **完整配置应该包含两个 server 块**：
   ```nginx
   # HTTP (80) - 重定向到 HTTPS
   server {
       listen 80;
       server_name luoshui.life;
       return 301 https://$server_name$request_uri;
   }
   
   # HTTPS (443) - 主服务
   server {
       listen 443 ssl http2;
       server_name luoshui.life;
       
       ssl_certificate /www/server/panel/vhost/cert/luoshui.life/fullchain.pem;
       ssl_certificate_key /www/server/panel/vhost/cert/luoshui.life/privkey.pem;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           ...
       }
   }
   ```

3. **保存并重启 Nginx**

### ✅ 第六步：测试 HTTPS

```bash
# 1. 浏览器访问
https://luoshui.life

# 2. 测试 API
https://luoshui.life/api/lof

# 3. 命令行测试
curl -I https://luoshui.life
```

**预期结果**：
- ✅ 浏览器显示安全锁图标 🔒
- ✅ 证书有效期显示 90 天
- ✅ API 正常返回数据

---

## 🚨 常见问题排查

### 问题 1：申请证书时仍然报 "Connection refused"

**原因**：Nginx 配置未生效

**解决**：
```bash
# SSH 连接服务器
sudo nginx -t  # 检查配置语法
sudo systemctl restart nginx  # 重启 Nginx
sudo netstat -tlnp | grep :80  # 确认 80 端口监听
```

### 问题 2：DNS TXT 记录验证失败

**原因**：使用了 DNS 验证方式

**解决**：
- 在宝塔面板中选择 **文件验证** 而不是 DNS 验证
- 或者在阿里云 DNS 控制台手动添加 TXT 记录

### 问题 3：证书申请成功但浏览器仍显示不安全

**原因**：Nginx 未配置 HTTPS (443 端口)

**解决**：
- 取消注释 `nginx-config-fixed.conf` 中的 HTTPS 部分
- 或在宝塔面板中勾选"强制 HTTPS"

---

## 📞 需要帮助？

如果遇到问题，请提供以下信息：

1. **Nginx 配置检查**
   ```bash
   sudo nginx -t
   ```

2. **端口监听检查**
   ```bash
   sudo netstat -tlnp | grep -E ':80|:443|:5000'
   ```

3. **Nginx 错误日志**
   ```bash
   sudo tail -50 /www/wwwlogs/happy-lof.error.log
   ```

4. **Let's Encrypt 日志**（如果有）
   ```bash
   sudo tail -50 /var/log/letsencrypt/letsencrypt.log
   ```

---

## 🎯 预计完成时间

- 第一步：5 分钟
- 第二步：10 分钟
- 第三步：2 分钟
- 第四步：5 分钟
- 第五步：5 分钟
- 第六步：3 分钟

**总计：约 30 分钟**

---

**最后提醒**：
1. 修改配置前建议备份原配置文件
2. 证书申请成功后，记得在小程序后台配置服务器域名
3. Let's Encrypt 证书有效期 90 天，宝塔面板会自动续期
