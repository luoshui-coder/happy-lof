# AGENTS.md

This file provides guidance to Codex when working with this repository.

## 项目概览

这是“今乐福”的阿里云部署版本：

- 后端：`app.py` 导出 Flask `app`，用于本地 API 调试或服务器侧按需挂载。
- 前端：`public/index.html` 静态页面，线上默认由阿里云服务器 nginx 托管。
- 数据源：首页实时列表使用集思录接口，核心逻辑封装在 `lof_lib.py`；基金详情历史曲线按需调用 Tushare。
- 持久化：无本地持久化，不使用 SQLite。
- 定时任务：无常驻 scheduler，不使用 APScheduler。

## 常用命令

安装依赖：

```bash
pip3 install -r requirements.txt
```

仅运行 Flask API：

```bash
flask --app app run --port 5003
```

部署：

```bash
# 线上默认部署到阿里云服务器 / 宝塔 / nginx，不走 Vercel。
```

## API

- `GET /api/health`：轻量健康检查，不请求集思录。
- `GET /api/lof`：实时 LOF 数据，前端负责筛选展示。
- `GET /api/lof/all`：非开放申购 LOF 数据。
- `GET /api/lof/<fund_id>/history`：按需返回 Tushare 场内价格和基金净值历史。

## 维护注意

- 不要重新引入 `database.py`、`scheduler.py`、SQLite 或长期运行脚本。
- 阿里云服务器环境变量按需配置 `JISILU_COOKIE`、`TUSHARE_TOKEN`。
- 不要把真实 Cookie、token、密钥写入仓库或回复。
- 静态资源放 `public/`，不要使用 Flask `static_folder`。
- 生产发布默认走阿里云服务器，不使用 Vercel 配置。
