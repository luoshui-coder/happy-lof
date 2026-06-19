# 今乐福

一个用于查询 LOF 基金实时溢价套利机会的 Web 工具。当前线上访问走国内阿里云服务器，由 nginx 托管 `public/` 静态资源；本仓库不再把 Vercel 作为默认部署路径。

## 功能

- 实时获取集思录 LOF 数据
- 支持指数 LOF、股票 LOF、QDII LOF、商品 QDII
- 前端展示“有利可套”和“全部数据”两个视图
- 支持点击基金按需查看 Tushare 场内价格、基金净值走势图和对照表
- 每 5 分钟自动刷新
- 支持集思录账号密码动态登录获取 Cookie，并返回鉴权状态，便于判断是否退化为游客数据

历史趋势功能按需调用 Tushare，不使用本地 SQLite 或后台定时任务。

## 项目结构

```text
happy-lof/
├── app.py              # Flask API 入口
├── lof_lib.py          # 集思录数据抓取、解析、筛选逻辑
├── public/
│   ├── index.html      # 前端页面
│   └── chicken.png     # 站点图标
├── requirements.txt    # Python 依赖
├── baota_lof_tencent_eastmoney_push.py  # 阿里云宝塔 Bark 推送脚本
└── .env.example        # 环境变量示例
```

## API

### `GET /api/health`

轻量健康检查，不请求集思录。

### `GET /api/lof`

返回实时 LOF 数据，由前端筛选“有利可套”列表。

### `GET /api/lof/all`

返回按溢价率排序的非开放申购 LOF 数据。

### `GET /api/lof/<fund_id>/history`

按需返回单只 LOF 的 Tushare 历史数据，包含：

- `price`：场内基金日线行情，来自 `fund_daily`
- `nav`：基金单位净值，来自 `fund_nav`
- `comparison`：按交易日合并的收盘价、最近已公布单位净值、价差和成交额

## 环境变量

只需要按需配置：

```bash
JISILU_USERNAME=""
JISILU_PASSWORD=""
JISILU_COOKIE_CACHE_TTL="3600"
JISILU_COOKIE=""
TUSHARE_TOKEN=""
```

优先配置 `JISILU_USERNAME`/`JISILU_PASSWORD` 动态登录获取 Cookie，避免固定 Cookie 过期导致实时列表被截断。`JISILU_COOKIE_CACHE_TTL` 是内存中动态 Cookie 的复用秒数，默认 3600。`JISILU_COOKIE` 仍可作为静态 Cookie 兜底；如果集思录登录触发验证码，会自动降级使用现有 Cookie 或游客态，并在接口返回的 `auth_status` 里提示。
未配置动态登录和静态 Cookie 时仍可运行，但集思录可能只返回游客态数据。
未配置 `TUSHARE_TOKEN` 时首页实时列表仍可运行，但基金详情历史曲线会提示缺少 Token。

## 本地开发

安装依赖：

```bash
pip3 install -r requirements.txt
```

启动 Flask API：

```bash
flask --app app run --port 5003
```

然后访问：

- API: `http://127.0.0.1:5003/api/health`
- API: `http://127.0.0.1:5003/api/lof`

静态页可直接打开 `public/index.html`，或通过 nginx/任意静态文件服务托管 `public/` 目录。

## 阿里云部署

当前公开页面地址：

- `http://8.134.134.156/happy-lof/`

生产环境优先通过阿里云服务器和宝塔/nginx 发布，不经过 Vercel。服务器侧按需配置 `JISILU_USERNAME`、`JISILU_PASSWORD`、`JISILU_COOKIE`、`TUSHARE_TOKEN`，不要把真实账号、密码、Cookie 或 Token 写入仓库。

## 设计约束

- 不使用 SQLite 或任何本地持久化文件。
- 不使用 APScheduler 或常驻后台任务。
- 历史接口只在用户点击基金详情时按需调用 Tushare。
- 静态资源放在 `public/`，不使用 Flask `static_folder`。
- 生产发布默认走阿里云服务器，不使用 Vercel 配置。
