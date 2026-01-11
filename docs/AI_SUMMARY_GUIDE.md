# GitHub Actions AI 总结功能使用指南

本文档介绍如何在 GitHub Actions 中配置和使用 AI 每日总结功能。

## 📋 功能概述

AI 总结功能会：
- 每天自动爬取热榜新闻
- 按关键词分组整理
- 调用 AI API 生成每日摘要
- 保存为 Markdown 文件
- 可选：发送到通知渠道

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv sync --group ai

# 或使用 pip
pip install openai anthropic
```

### 2. 配置 GitHub Secrets

进入 GitHub 仓库：`Settings → Secrets and variables → Actions`

#### 必需的 Secrets

| Secret 名称 | 说明 | 示例值 |
|-------------|------|--------|
| `AI_PROVIDER` | AI 服务商 | `openai` / `anthropic` |
| `AI_API_KEY` | API 密钥 | `nvapi-...` / `sk-ant-...` |
| `AI_MODEL` | 模型名称 | `meta/llama-3.1-405b-instruct` |

#### 可选的 Secrets

| Secret 名称 | 说明 | 示例值 |
|-------------|------|--------|
| `AI_BASE_URL` | API 端点 | `https://integrate.api.nvidia.com/v1` |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook | `https://open.feishu.cn/...` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot | `your-bot-token` |
| `TELEGRAM_CHAT_ID` | Telegram 聊天 ID | `your-chat-id` |

### 3. 支持的 AI 服务商

#### NVIDIA NIM（推荐，免费额度）

```bash
AI_PROVIDER=openai
AI_API_KEY=nvapi-...
AI_BASE_URL=https://integrate.api.nvidia.com/v1
AI_MODEL=meta/llama-3.1-405b-instruct
```

获取 API Key: https://build.nvidia.com/

#### Anthropic Claude

```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-api03-...
AI_MODEL=claude-3-5-sonnet-20241022
```

#### OpenAI

```bash
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4
```

#### DeepSeek

```bash
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat
```

### 4. 启用 Workflow

Workflow 文件：`.github/workflows/ai-summary.yml`

#### 定时执行

默认：每天北京时间 22:30 自动运行

```yaml
schedule:
  - cron: "30 14 * * *"  # UTC 14:30 = 北京 22:30
```

修改时间：
- 只改第一个数字（0-59）表示分钟
- `30 0-14 * * *` = 北京 8:00-22:00 每小时第30分钟

#### 手动触发

1. 进入 GitHub Actions 页面
2. 选择 `AI Daily Summary` workflow
3. 点击 `Run workflow` → `Run workflow`

### 5. 查看结果

#### 方式一：Actions 日志

1. 进入 Actions 页面
2. 选择 `AI Daily Summary` 运行记录
3. 展开步骤查看生成的摘要

#### 方式二：下载 Artifact

每次运行会生成：
- 文件名：`ai-summary-{run_number}`
- 包含：`summary_{timestamp}.md`
- 保留：30 天

## 🧪 本地测试

### 测试 AI 总结脚本

```bash
# 设置环境变量
export AI_PROVIDER=openai
export AI_API_KEY=your-api-key
export AI_BASE_URL=https://integrate.api.nvidia.com/v1
export AI_MODEL=meta/llama-3.1-405b-instruct

# 先运行爬虫获取数据
python -m trendradar

# 生成 AI 总结
python scripts/generate_ai_summary.py
```

### 查看生成的文件

```bash
ls output/ai_summaries/
# summary_20260111_183000.md
```

## 📝 生成的摘要格式

```markdown
# AI 每日摘要

生成时间: 2026-01-11 18:30:00

## 中国 (7条)
- 中方赞赏斡印努力，期待双方落实共识 (新华社) https://...
- 中国搜救队成功完成全球数据7天任务 (人民日报) https://...

## 美国 (3条)
- 美国一导弹系统部署引发争议 (CNN) https://...

... (按关键词分组)
```

## ⚙️ 高级配置

### 自定义提示词

编辑 `.env` 文件：

```env
AI_SUMMARY_PROMPT_TEMPLATE= |
  请用简洁的语言总结今日热点，
  每个关键词不超过50字，
  最后给出3条推荐阅读。
```

### 调整摘要长度

```env
AI_MAX_NEWS_PER_KEYWORD=5   # 每个关键词最多5条新闻
AI_MODEL=gpt-4-turbo        # 使用更快的模型
```

### 发送到通知渠道

确保已配置通知 Secrets（如 `FEISHU_WEBHOOK_URL`），workflow 会自动发送。

## 🔧 故障排查

### 问题：Workflow 运行但没有生成摘要

**检查：**
1. Actions 日志中的错误信息
2. AI_API_KEY 是否正确配置
3. 是否有新闻数据（需要先运行爬虫）

### 问题：AI API 调用失败

**错误：** `AI API call failed`

**解决：**
1. 检查 API Key 是否有效
2. 检查 BASE_URL 是否正确
3. 检查模型名称是否正确
4. 查看完整的错误日志

### 问题：摘要内容为空

**原因：** 没有匹配关键词的新闻

**解决：**
1. 检查 `config/frequency_words.txt` 配置
2. 确认爬虫已成功运行
3. 查看 MCP 工具 `get_trending_topics` 确认数据

## 📊 成本估算

使用 NVIDIA NIM（免费额度）：
- 每天 1 次调用
- 每次 ~1000 tokens
- 免费额度内足够使用

使用其他服务商：
- OpenAI GPT-4: ~$0.01-0.03/天
- Anthropic Claude: ~$0.01-0.02/天
- DeepSeek: ~$0.0001/天

## 🔗 相关链接

- [NVIDIA NIM](https://build.nvidia.com/)
- [OpenAI API](https://platform.openai.com/)
- [Anthropic Claude](https://console.anthropic.com/)
- [DeepSeek](https://platform.deepseek.com/)

## 💡 最佳实践

1. **使用 NVIDIA NIM** - 有免费额度，性价比高
2. **设置每日时间** - 爬虫运行后 30 分钟
3. **保存 Artifact** - 方便查看历史记录
4. **配置通知** - 及时获取摘要推送

---

需要帮助？请查看 [主文档](../README.md) 或提交 Issue。
