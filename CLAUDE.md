# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

这是一个用于查询 LOF 基金溢价套利机会的 Web 工具：
- 后端：Flask 提供 API，并托管静态前端页面。
- 前端：`static/index.html` 单页展示与轮询刷新。
- 数据源：集思录（Jisilu）接口，封装在 `lof_lib.py`。
- 持久化：SQLite（`lof_history.db`）记录每日溢价数据，用于历史趋势。
- 定时任务：APScheduler 后台任务每日固定时间写入历史数据。

## 常用命令

### 安装依赖

```bash
pip3 install -r requirements.txt
```

### 启动服务

```bash
python3 app.py
```

或使用启动脚本（会按需安装依赖）：

```bash
./start.sh
```

启动后访问：
- 页面：`http://127.0.0.1:5003/`
- API：`http://127.0.0.1:5003/api/lof`

### 运行“测试”

该仓库未提供自动化测试用例或测试命令。

## 架构与代码流（大图）

### 1) Flask 入口与路由

- `app.py`：应用入口，创建 Flask app，启用 CORS，并在进程启动时初始化：
  - `LOFDatabase()`（SQLite 初始化）
  - `LOFScheduler().start()`（启动 APScheduler 后台定时任务）
  - `JisiluAPI()`（集思录 API 客户端）

主要路由：
- `GET /`：返回 `static/index.html`。
- `GET /api/lof`：拉取全量 LOF → 使用 `filter_lof()` 按阈值筛选套利机会。
- `GET /api/lof/all`：拉取全量 LOF → 仅排除开放申购 → 按溢价率排序。
- `GET /api/lof/history/<fund_id>?days=30`：读取 SQLite 的历史记录。

### 2) 数据抓取与筛选

- `lof_lib.py`：核心领域逻辑与数据模型
  - `LOFInfo`：基金数据结构（dataclass）。
  - `JisiluAPI`：封装集思录请求（Session + headers + timeout），聚合三类数据源：
    - 指数 LOF：`/data/lof/index_lof_list/`
    - QDII LOF：`/data/qdii/qdii_list/E`
    - 商品 QDII：`/data/qdii/qdii_list/C`
  - `filter_lof()`：根据溢价率、成交额、申购状态过滤并排序。

### 3) 历史数据落库与查询

- `database.py`：`LOFDatabase`
  - 表：`premium_history`（`fund_id + record_date` 唯一）
  - `save_daily_data()`：按天 `INSERT OR REPLACE` 写入。
  - `get_history()`：按日期倒序取最近 N 天，返回给 API 时再倒序（旧→新）。

### 4) 定时任务

- `scheduler.py`：`LOFScheduler`
  - 使用 `BackgroundScheduler()` 注册 cron job：每天 `14:55` 调用 `record_daily_data()`。
  - `record_daily_data()`：抓取全量 LOF → 只保留 `premium_rate > 0` → 写入 SQLite。

## 前端位置

- `static/index.html`：静态单页，调用后端 API 展示数据并自动刷新。
- `static/chicken.png`：站点图标/素材。
