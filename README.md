# 今乐福 (Happy LOF)

💰 LOF 基金套利溢价查询工具

## 简介

今乐福是一个 LOF（上市型开放式基金）套利溢价查询工具，帮助投资者快速发现高溢价套利机会。

## 功能特性

- ✅ 实时获取集思录 LOF 数据
- ✅ 智能筛选套利机会（溢价率≥1%，成交额≥1000万，非开放申购）
- ✅ 支持指数LOF、QDII、商品基金
- ✅ 精美的移动端友好界面
- ✅ 自动每5分钟刷新数据
- ✅ 历史溢价率趋势记录
- ✅ 显示交易所信息（深/沪）

## 快速开始

### 安装依赖

```bash
pip3 install -r requirements.txt
```

### 启动服务

```bash
python3 app.py
```

或使用启动脚本：

```bash
./start.sh
```

### 访问页面

在浏览器中打开：http://127.0.0.1:5003

## 项目结构

```
LOF 基金套利/
├── app.py                 # Flask 后端服务
├── database.py            # SQLite 数据库管理
├── scheduler.py           # 定时任务调度（每天 14:55 记录数据）
├── static/
│   └── index.html         # 前端页面
├── requirements.txt       # 依赖文件
├── start.sh              # 启动脚本
└── README.md             # 说明文档
```

## API 接口

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

## 数据来源

数据来自：**集思录** (https://www.jisilu.cn)
- 指数 LOF
- QDII LOF
- 商品 QDII

## 注意事项

1. 数据仅供参考，投资有风险
2. 建议看到高溢价机会后再到券商 APP 确认
3. 注意区分深圳和上海交易所的基金

## 技术栈

- **后端**: Python + Flask
- **前端**: HTML + CSS + JavaScript
- **数据源**: 集思录 API

## License

MIT
