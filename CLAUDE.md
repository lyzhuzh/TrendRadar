# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

TrendRadar（热点助手）是一个基于 Python 的热点新闻聚合与分析工具，具有以下特性：
- 爬取 11+ 个中文平台的热点新闻（今日头条、雪球、微博、知乎、B站等）
- 获取自定义 RSS 订阅源的内容，支持新鲜度过滤
- 通过 MCP（模型上下文协议）服务器提供 AI 驱动的分析功能
- 向 8+ 个通知渠道发送推送（微信、Telegram、钉钉、邮件等）
- 支持本地和云存储（兼容 AWS S3/Cloudflare R2）

**Python 版本要求：** 3.10+
**当前版本：** 4.6.0

## 常用命令

### 运行应用
```bash
# 主爬虫程序（抓取热榜并发送通知）
python -m trendradar

# MCP 服务器（stdio 模式 - 用于 AI 集成，如 Claude Desktop）
python -m mcp_server.server

# MCP 服务器（HTTP 模式 - 用于生产环境）
python -m mcp_server.server --transport http --port 3333

# 安装后的命令行工具
trendradar              # 等同于 python -m trendradar
trendradar-mcp          # 等同于 python -m mcp_server.server
```

### 安装和设置
```bash
# 使用 UV（推荐）
pip install uv
uv sync

# 使用 pip（传统方式）
pip install -e .

# 安装后验证
trendradar --help
trendradar-mcp --help
```

### Docker
```bash
# 构建镜像
docker build -t trendradar .

# 运行容器（挂载配置目录）
docker run -v $(pwd)/config:/app/config trendradar
```

## 架构设计

### 双组件结构

**1. 主程序 (`trendradar/`)**
- 入口：`trendradar/__main__.py`
- 核心爬虫，负责抓取和处理新闻
- 生成 HTML 报告并发送通知
- 三种报告模式：`daily`（日报）、`current`（当前榜单）、`incremental`（增量监控）

**2. MCP 服务器 (`mcp_server/`)**
- 入口：`mcp_server/server.py`
- 基于 FastMCP 2.0 的 AI 集成服务器
- 提供 20+ 个新闻分析和查询工具
- 支持 stdio 和 HTTP 两种传输模式

### 核心目录结构

```
trendradar/
├── __main__.py          # 主入口（NewsAnalyzer 类）
├── context.py           # AppContext - 应用程序中心状态管理
├── core/               # 核心逻辑
│   ├── analyzer.py      # 新闻分析和频率统计
│   ├── config.py        # ConfigSchema 配置定义
│   ├── data.py          # 数据结构（NewsData、RSSData）
│   ├── frequency.py     # 关键词匹配
│   └── loader.py        # 配置加载
├── crawler/             # 数据采集
│   ├── fetcher.py      # DataFetcher - 主爬虫
│   └── rss/            # RSS 专用爬虫
├── notification/        # 通知系统
│   ├── dispatcher.py    # 多渠道分发器
│   ├── senders.py      # 各渠道发送器
│   └── renderer.py     # 消息格式化
├── report/             # 报告生成
│   ├── html.py         # HTML 报告生成器
│   └── rss_html.py     # RSS 订阅生成器
├── storage/            # 存储后端
│   ├── base.py         # 存储接口基类
│   ├── local.py        # 本地文件存储
│   └── remote.py      # S3 兼容云存储
└── utils/              # 工具函数
    ├── time.py         # 时区处理
    └── url.py          # URL 工具

mcp_server/
├── server.py           # MCP 服务器（FastMCP 2.0）
├── tools/              # AI 工具（20+ 接口）
│   ├── analytics.py    # 趋势/情感分析
│   ├── data_query.py   # 数据检索
│   ├── search_tools.py # 搜索功能
│   ├── config_mgmt.py  # 配置管理
│   ├── system.py       # 系统管理
│   └── storage_sync.py # 云存储同步
├── services/           # 业务逻辑
│   ├── cache_service.py
│   ├── data_service.py
│   └── parser_service.py
└── utils/
    ├── date_parser.py  # 自然语言日期解析
    └── errors.py       # MCP 错误处理
```

### 配置系统

**主配置文件：** `config/config.yaml`

主要配置节：
- `app`：时区（默认 Asia/Shanghai）、版本检查
- `platforms`：新闻平台定义（id、name）
- `rss`：RSS 订阅源配置，支持新鲜度过滤（freshness_filter）
- `report`：报告模式（daily/current/incremental）、显示选项
- `notification`：8+ 通知渠道，支持多账号（用分号分隔）
- `storage`：后端选择（local/remote/auto）、保留策略（retention_days）
- `push_window`：推送时间窗口控制（time_range、once_per_day）

**关键词文件：** `config/frequency_words.txt`
- 按类别组织，带优先级
- 用于过滤和高亮新闻
- 支持全局过滤词（global_filters）

### 报告模式（核心概念）

应用有三种不同的报告模式，会影响运行行为：

1. **`incremental`（增量监控）** - 仅在有新的匹配新闻时推送
2. **`current`（当前榜单）** - 推送当前排名，包含全天累计数据
3. **`daily`（日报汇总）** - 推送完整的日报摘要

模式在 `config.yaml` 的 `report.mode` 中设置，会影响：
- 通知中包含哪些数据
- 通知何时触发
- 统计数据如何计算

### 数据流程

1. **爬取阶段：** `DataFetcher` 爬取所有配置的平台
2. **存储：** 数据保存到 SQLite（本地）或 S3（远程）
   - 热榜数据：`NewsData` 格式（platform, id, title, url, rank, crawl_time）
   - RSS 数据：`RSSData` 格式（feed_id, title, url, published_at, summary）
3. **分析：** `analyzer.count_frequency()` 匹配关键词
4. **报告生成：** 如果启用则创建 HTML 报告
5. **通知：** `NotificationDispatcher` 发送到配置的渠道

### 数据存储结构

**热榜数据**（`storage/base.py` 中的 `NewsData`）：
- `date`: 抓取日期（YYYY-MM-DD 格式）
- `crawl_time`: 抓取时间戳
- `platforms`: 平台数据字典
- `id_to_name`: 平台ID到名称的映射
- `failed_ids`: 抓取失败的平台列表

**RSS 数据**（`storage/base.py` 中的 `RSSData`）：
- `date`: 抓取日期
- `items`: RSS 条目字典（按 feed_id 组织）
- `id_to_name`: RSS 源ID到名称的映射

### MCP 服务器工具

MCP 服务器提供 20+ 个工具，分为以下类别：
- **日期解析：** `resolve_date_range()` - 处理自然语言日期时优先调用
- **数据查询：** `get_latest_news()`、`get_news_by_date()`、`get_trending_topics()`、`get_news_for_summary()`
- **RSS 查询：** `get_latest_rss()`、`search_rss()`、`get_rss_feeds_status()`
- **搜索：** `search_news()`（支持 keyword/fuzzy/entity 模式）、`find_related_news()`
- **分析：** `analyze_topic_trend()`（支持 trend/lifecycle/viral/predict）、`analyze_sentiment()`、`aggregate_news()`、`compare_periods()`
- **系统：** `trigger_crawl()`、`get_system_status()`、`get_storage_status()`
- **存储同步：** `sync_from_remote()`、`list_available_dates()`

## 重要设计模式

1. **AppContext 模式** - 在 `trendradar/context.py` 中集中管理状态
   - 提供统一的配置访问接口（timezone、platforms、weight_config 等）
   - 封装存储管理器、通知分发器等组件的创建
   - 消除对全局 CONFIG 的依赖

2. **存储抽象** - 通过 `storage/base.py` 实现可插拔后端
   - `local.py`: 本地 SQLite 存储
   - `remote.py`: S3 兼容云存储（支持 Cloudflare R2）
   - 自动模式：根据环境变量自动选择后端

3. **渠道插件系统** - 通知发送器位于 `notification/senders.py`
   - 每个渠道独立实现发送逻辑
   - `NotificationDispatcher` 负责多渠道分发
   - 支持消息分批（`split_content_into_batches`）

4. **模式策略模式** - 报告行为在 `__main__.py` 的 MODE_STRATEGIES 中定义
   - incremental: 仅在有新增时推送
   - current: 推送当前榜单（含全天累计）
   - daily: 推送完整日报

5. **配置驱动** - 大部分行为通过 `config.yaml` 控制
   - 环境变量可覆盖配置（如 STORAGE_RETENTION_DAYS）
   - 支持多账号配置（分号分隔）

## 时区处理

所有时间使用配置中的 `app.timezone`（默认：Asia/Shanghai）。
- 使用 `ctx.get_time()` 获取当前时间
- 使用 `ctx.format_time()` 格式化时间戳
- 使用 `ctx.format_date()` 获取日期字符串

## 通知渠道

多账号支持（用分号 `;` 分隔）：
- 企业微信：`notification.wework.webhook_url`、`msg_type`
- 钉钉：`notification.dingtalk.webhook_url`
- 飞书：`notification.feishu.webhook_url`
- Telegram：`notification.telegram.bot_token`、`chat_id`
- 邮箱：`notification.email.from`、`password`、`to`（逗号分隔多个收件人）
- ntfy：`notification.ntfy.server_url`、`topic`、`token`
- Bark：`notification.bark.url`
- Slack：`notification.slack.webhook_url`

## 测试 MCP 服务器

```bash
# 测试 stdio 模式
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m mcp_server.server

# 测试 HTTP 模式
curl http://localhost:3333/mcp -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 常见修改

- **添加新闻平台：** 编辑 `config/config.yaml` 中的平台列表，在 `crawler/` 中实现爬虫
- **添加通知渠道：** 在 `notification/senders.py` 添加发送器，在 `dispatcher.py` 中注册
- **修改报告格式：** 修改 `report/html.py`（HTML）或 `notification/renderer.py`（消息）
- **添加关键词类别：** 编辑 `config/frequency_words.txt`
- **添加 MCP 工具：** 在 `mcp_server/tools/` 中创建工具类，在 `server.py` 中注册

## CI/CD

GitHub Actions 工作流（`.github/workflows/crawler.yml`）：
- 调度：每小时第 30 分钟运行（北京时间 8:00-22:00）
- 使用环境变量配置敏感信息（webhook、API 密钥）
- 自动版本检查
- 支持通过环境变量覆盖配置（如 `STORAGE_RETENTION_DAYS`）

## 故障排查

### 通知未发送
1. 检查 `notification.enabled` 是否为 `true`
2. 检查至少配置了一个通知渠道
3. 检查推送窗口设置（`push_window`）
4. 检查报告模式下的内容匹配逻辑（incremental 模式需要新增内容）

### MCP 服务器连接失败
1. stdio 模式：检查 Claude Desktop 的 MCP 配置文件路径
2. HTTP 模式：检查端口是否被占用，使用 `--port` 指定其他端口
3. 查看服务器日志确认启动状态

### 爬虫失败
1. 检查网络连接和代理配置（`USE_PROXY`、`DEFAULT_PROXY`）
2. 检查平台配置的 `id` 是否正确
3. GitHub Actions 环境会自动禁用代理

### 数据未保存
1. 检查存储后端配置（`storage.backend`）
2. 检查 `storage.formats` 中的格式是否启用
3. 远程存储需要配置环境变量（`S3_ENDPOINT_URL`、`S3_BUCKET_NAME` 等）
