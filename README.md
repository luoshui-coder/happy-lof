# 今乐福 (Happy LOF) 💰

> 一个精美的 LOF 基金套利溢价查询工具，支持 Web 和微信小程序双端访问

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![WeChat MiniProgram](https://img.shields.io/badge/WeChat-MiniProgram-07C160.svg)](https://developers.weixin.qq.com/miniprogram/dev/framework/)

## 📖 项目简介

**今乐福** 是一个专为 LOF（Listed Open-ended Fund，上市型开放式基金）套利设计的实时监控工具。通过智能筛选和精美的可视化界面，帮助投资者快速发现和把握套利机会。

**现已支持：**
- 🌐 **Web 版本**：响应式网页，支持桌面和移动端浏览器
- 📱 **小程序版本**：微信小程序，原生体验更流畅

### 🎯 核心价值

- **实时监控**：自动获取集思录最新 LOF 数据，Web 版每 5 分钟自动刷新
- **智能筛选**：基于溢价率、成交额、申购状态等多维度筛选套利机会
- **历史追踪**：记录每日溢价率数据，绘制历史趋势图
- **移动优先**：精美的响应式设计，完美适配手机端
- **套利评级**：智能计算套利难度，用星级直观展示
- **双端支持**：Web + 小程序，随时随地查看套利机会

## ✨ 功能特性

### 核心功能

- ✅ **实时数据获取**：从集思录获取指数 LOF、QDII、商品基金等数据
- ✅ **智能筛选**：溢价率 ≥1%，成交额 ≥1000万，排除开放申购基金
- ✅ **套利难度评级**：基于溢价率、成交额、基金类型的智能评分系统（⭐-⭐⭐⭐⭐⭐）
- ✅ **历史趋势图**：每日记录溢价率，绘制 30 天历史走势
- ✅ **交易所标识**：清晰显示深圳/上海交易所及持有天数（T+2/T+3）
- ✅ **一键复制**：点击基金代码即可复制，方便快速下单
- ✅ **自动刷新**：Web 版每 5 分钟自动更新，小程序支持下拉刷新

### 界面特色

- 🎨 **精美设计**：渐变色卡片、流畅动画、现代化 UI
- 📱 **移动优先**：完美适配手机、平板、桌面端
- 🌈 **可视化**：ECharts/Chart.js 绘制历史溢价率趋势图
- 🚀 **流畅体验**：悬浮刷新按钮、Toast 提示、加载动画

## 🚀 快速开始

### 后端服务部署

#### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 2. 启动服务

```bash
python3 app.py
```

或使用启动脚本：

```bash
./start.sh
```

#### 3. 访问 Web 版

在浏览器中打开：http://127.0.0.1:5000

### 小程序部署

详细部署指南请查看：[miniprogram/README.md](./miniprogram/README.md)

**快速步骤：**

1. 配置后端 API 地址（需 HTTPS）
2. 配置小程序 AppID
3. 使用微信开发者工具打开 `miniprogram` 目录
4. 预览或上传代码

> ⚠️ **重要**：小程序要求后端必须使用 HTTPS 协议

## 📁 项目结构

```
happy-lof/
├── app.py                 # Flask 后端服务
├── lof_lib.py             # LOF 核心逻辑库
├── database.py            # SQLite 数据库管理
├── scheduler.py           # 定时任务调度（每天 14:55 记录数据）
├── static/
│   └── index.html         # Web 前端页面
├── miniprogram/           # 微信小程序
│   ├── pages/             # 页面
│   │   ├── index/         # 首页（基金列表）
│   │   └── detail/        # 详情页
│   ├── components/        # 组件
│   │   └── fund-card/     # 基金卡片组件
│   ├── utils/             # 工具函数
│   │   ├── api.js         # API 请求封装
│   │   └── util.js        # 通用工具
│   └── libs/              # 第三方库
│       └── ec-canvas/     # ECharts 图表组件
├── requirements.txt       # Python 依赖
├── 宝塔部署指南.md        # 服务器部署指南
└── README.md             # 本文档
```

## 🔌 API 接口

### 获取高溢价套利数据

```
GET /api/lof
```

筛选条件：
- 溢价率 >= 1%
- 成交额 >= 1000万
- 非开放申购状态

### 获取全部数据

```
GET /api/lof/all
```

### 获取历史溢价数据

```
GET /api/lof/history/<fund_id>?days=30
```

参数：
- `fund_id`: 基金代码
- `days`: 查询天数（默认 30 天）

## 🌐 部署指南

### Web 版部署

#### 方式一：宝塔面板部署（推荐）

详细步骤请查看：[宝塔部署指南.md](./宝塔部署指南.md)

**最简单的方式**：使用宝塔 **Python项目管理器**
1. 安装 Python 项目管理器插件
2. 添加项目，填写路径和启动文件
3. 一键启动，支持开机自启

#### 方式二：直接运行

```bash
# 使用生产环境脚本
chmod +x start_prod.sh
./start_prod.sh
```

### 小程序部署

详细步骤请查看：[miniprogram/README.md](./miniprogram/README.md)

**关键步骤：**
1. 配置 HTTPS（必须）
2. 配置域名白名单
3. 上传代码审核
4. 发布上线

## ⚙️ 环境变量配置

支持以下环境变量：

- `PORT`: 应用端口（默认 5000）
- `DEBUG`: 调试模式（默认 False）
- `TZ`: 时区（默认 Asia/Shanghai）

示例：
```bash
export PORT=8080
export DEBUG=False
python3 app.py
```

## ⏰ 定时任务配置

为了记录每日溢价率数据，需要配置定时任务：

```bash
# 每天 14:55 执行数据采集
55 14 * * * cd /path/to/project && python3 database.py
```

宝塔面板用户可在 **计划任务** 中添加 Shell 脚本。

## ⚠️ 注意事项

1. 数据仅供参考，投资有风险
2. 建议看到高溢价机会后再到券商 APP 确认
3. 注意区分深圳和上海交易所的基金
4. 小程序部署需要 HTTPS 和已备案域名

## 📊 数据来源

数据来自：**集思录** (https://www.jisilu.cn)
- 指数 LOF
- QDII LOF
- 商品 QDII

## 🛠️ 技术栈

### 后端
- **框架**: Python + Flask
- **数据库**: SQLite
- **数据源**: 集思录 API
- **定时任务**: APScheduler

### Web 前端
- **技术**: HTML + CSS + JavaScript
- **图表**: Chart.js
- **设计**: 响应式布局、渐变色、动画

### 小程序前端
- **框架**: 微信小程序原生
- **语言**: WXML + WXSS + JavaScript
- **图表**: ECharts for WeChat
- **组件**: 自定义组件化开发

## 📸 截图预览

### Web 版
- 精美的渐变色设计
- 实时溢价率显示
- 历史趋势背景图

### 小程序版
- 原生小程序体验
- 下拉刷新
- ECharts 趋势图

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT

---

**开发者**: luoshui-coder  
**项目地址**: https://github.com/luoshui-coder/happy-lof
