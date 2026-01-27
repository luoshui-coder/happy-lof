# 今乐福小程序部署指南

本文档介绍如何部署和运行今乐福微信小程序。

## 📋 前置要求

### 1. 微信小程序账号
- 注册微信小程序账号：https://mp.weixin.qq.com
- 获取 AppID（在小程序后台 → 开发 → 开发设置中查看）

### 2. 开发工具
- 下载并安装微信开发者工具：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
- 版本要求：建议使用最新稳定版

### 3. 后端服务
- 确保 Flask 后端服务已部署并运行
- **必须配置 HTTPS**（小程序要求）
- 已备案的域名

## 🚀 快速开始

### 步骤 1：配置后端 API 地址

编辑 `miniprogram/app.js`，修改 API 地址：

```javascript
globalData: {
  // 生产环境：使用 HTTPS 域名
  apiBase: 'https://your-domain.com/api',
  
  // 开发环境：可以使用 HTTP（需在开发者工具中开启"不校验合法域名"）
  // apiBase: 'http://127.0.0.1:5000/api'
}
```

### 步骤 2：配置小程序 AppID

编辑 `miniprogram/project.config.json`，修改 appid：

```json
{
  "appid": "你的小程序AppID"
}
```

### 步骤 3：打开项目

1. 启动微信开发者工具
2. 选择"导入项目"
3. 项目目录选择：`/path/to/happy-lof/miniprogram`
4. AppID：填写你的小程序 AppID（或选择测试号）

### 步骤 4：开发调试

#### 开启本地调试（开发环境）

在微信开发者工具中：
1. 点击右上角"详情"
2. 勾选"不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"
3. 这样可以在开发时使用 HTTP 协议访问本地后端

#### 真机预览

1. 点击工具栏"预览"按钮
2. 使用微信扫描二维码
3. 在手机上查看效果

> ⚠️ **注意**：真机预览时必须使用 HTTPS，否则会报网络请求失败

## 🔧 后端 HTTPS 配置

### 方式一：宝塔面板配置 SSL

1. 登录宝塔面板
2. 进入"网站" → 选择你的站点
3. 点击"SSL" → 选择证书类型：
   - **Let's Encrypt**（免费，推荐）
   - 其他证书（购买的证书）
4. 申请并部署证书
5. 开启"强制 HTTPS"

### 方式二：Nginx 手动配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 🌐 配置服务器域名白名单

在微信公众平台配置合法域名：

1. 登录微信公众平台：https://mp.weixin.qq.com
2. 进入"开发" → "开发管理" → "开发设置"
3. 找到"服务器域名"，点击"修改"
4. 配置以下域名：

| 类型 | 域名 |
|------|------|
| request 合法域名 | `https://your-domain.com` |
| uploadFile 合法域名 | （如需上传功能则配置） |
| downloadFile 合法域名 | （如需下载功能则配置） |

> ⚠️ **重要提示**：
> - 域名必须使用 HTTPS 协议
> - 域名必须已备案
> - 每月只能修改 5 次，请谨慎操作

## 📦 项目结构

```
miniprogram/
├── app.js                  # 小程序入口
├── app.json                # 全局配置
├── app.wxss                # 全局样式
├── project.config.json     # 项目配置
├── sitemap.json            # 索引配置
├── pages/
│   ├── index/              # 首页（基金列表）
│   │   ├── index.js
│   │   ├── index.json
│   │   ├── index.wxml
│   │   └── index.wxss
│   └── detail/             # 详情页
│       ├── detail.js
│       ├── detail.json
│       ├── detail.wxml
│       └── detail.wxss
├── components/
│   └── fund-card/          # 基金卡片组件
│       ├── fund-card.js
│       ├── fund-card.json
│       ├── fund-card.wxml
│       └── fund-card.wxss
├── utils/
│   ├── api.js              # API 请求封装
│   └── util.js             # 工具函数
└── libs/
    └── ec-canvas/          # ECharts 图表组件
        ├── ec-canvas.js
        ├── ec-canvas.json
        ├── ec-canvas.wxml
        ├── ec-canvas.wxss
        └── echarts.js      # ECharts 库（1MB）
```

## 🧪 功能测试清单

- [ ] 基金列表正常加载
- [ ] 下拉刷新可用
- [ ] 溢价率数据正确显示
- [ ] 套利评级星级显示
- [ ] 点击基金代码可复制
- [ ] 点击卡片跳转详情页
- [ ] 详情页历史趋势图正常显示
- [ ] 真机测试网络请求正常

## 📱 发布上线

### 1. 代码审核

1. 在微信开发者工具中点击"上传"
2. 填写版本号和项目备注
3. 上传成功后，登录微信公众平台
4. 进入"版本管理" → "开发版本"
5. 选择刚上传的版本，点击"提交审核"

### 2. 审核材料准备

- 小程序名称、图标、简介
- 服务类目（选择"金融 → 基金"）
- 隐私政策链接（必填）
- 用户协议链接（可选）

### 3. 审核通过后发布

- 审核通过后会收到通知
- 在"版本管理"中点击"发布"
- 发布后用户即可搜索使用

## ⚠️ 常见问题

### 1. 网络请求失败

**问题**：小程序提示"request:fail"

**解决方案**：
- 检查后端是否使用 HTTPS
- 检查域名是否在白名单中
- 开发环境：开启"不校验合法域名"

### 2. ECharts 图表不显示

**问题**：详情页趋势图空白

**解决方案**：
- 检查 `echarts.js` 文件是否存在
- 检查微信基础库版本 >= 2.9.0
- 查看控制台是否有错误信息

### 3. 数据加载慢

**问题**：首页加载时间过长

**解决方案**：
- 优化后端 API 响应速度
- 使用 CDN 加速
- 考虑添加缓存机制

### 4. 小程序包过大

**问题**：代码包超过 2MB 限制

**解决方案**：
- 使用分包加载
- 压缩图片资源
- 考虑将 ECharts 放入分包

## 🔄 后续优化建议

1. **性能优化**
   - 添加数据缓存
   - 使用分包加载
   - 图片懒加载

2. **功能增强**
   - 添加基金收藏功能
   - 推送通知（高溢价提醒）
   - 数据筛选和排序

3. **用户体验**
   - 添加骨架屏
   - 优化加载动画
   - 支持暗黑模式

## 📞 技术支持

如有问题，请查看：
- 微信小程序官方文档：https://developers.weixin.qq.com/miniprogram/dev/framework/
- ECharts 小程序版：https://github.com/ecomfe/echarts-for-weixin
- 项目 GitHub：https://github.com/luoshui-coder/happy-lof

## 📄 许可证

MIT License
