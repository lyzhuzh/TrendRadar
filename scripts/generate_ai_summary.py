# coding=utf-8
"""
AI 总结脚本 - 用于 GitHub Actions
从数据库读取今日新闻并调用 AI API 生成总结
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trendradar.core import load_config
from trendradar.context import AppContext
from mcp_server.tools.data_query import DataQueryTools


def generate_ai_summary():
    """生成 AI 总结"""
    print("Generating AI summary...")

    # 加载配置
    config = load_config()
    ai_config = config.get("AI", {})

    provider = ai_config.get("PROVIDER", "openai")
    api_key = ai_config.get("API_KEY", "")
    base_url = ai_config.get("BASE_URL", "")
    model = ai_config.get("MODEL", "gpt-4")

    if not api_key:
        print("[ERROR] AI_API_KEY not configured")
        return None

    # 获取今日新闻数据
    tools = DataQueryTools()
    result = tools.get_news_for_summary(
        mode="current",
        group_by="keyword",
        max_news_per_keyword=10,
        include_url=True
    )

    if not result.get("success"):
        print(f"[ERROR] {result.get('error', {}).get('message')}")
        return None

    # 构建 AI 提示
    summary_data = result.get("keyword_groups", [])
    prompt = build_summary_prompt(summary_data)

    # 调用 AI API
    summary = call_ai_api(provider, api_key, base_url, model, prompt)

    return summary


def build_summary_prompt(keyword_groups):
    """构建 AI 提示词"""
    prompt = "请根据以下热点新闻数据生成每日摘要。\n\n"
    prompt += "按关键词分组，每组用 1-2 句话总结，最后列出相关链接。\n\n"

    for group in keyword_groups[:10]:  # 最多 10 个关键词
        keyword = group.get("keyword")
        count = group.get("count")
        news_list = group.get("news", [])

        prompt += f"## {keyword} ({count}条)\n"

        for news in news_list[:3]:  # 每个关键词最多 3 条
            title = news.get("title")
            source = news.get("source_name")
            url = news.get("url", "")

            prompt += f"- {title} ({source})"
            if url:
                prompt += f" {url}"
            prompt += "\n"

        prompt += "\n"

    prompt += "\n请生成简洁的摘要，突出重点。"
    return prompt


def call_ai_api(provider, api_key, base_url, model, prompt):
    """调用 AI API"""
    try:
        if provider == "openai" or base_url:  # 兼容 OpenAI 格式
            from openai import OpenAI

            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url

            client = OpenAI(**client_kwargs)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个新闻摘要助手，擅长提炼要点。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message.content

        elif provider == "anthropic":
            from anthropic import Anthropic

            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url

            client = Anthropic(**client_kwargs)

            response = client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        else:
            print(f"[ERROR] Unsupported provider: {provider}")
            return None

    except Exception as e:
        print(f"[ERROR] AI API call failed: {e}")
        return None


def save_summary_to_file(summary):
    """保存总结到文件"""
    if not summary:
        return

    from datetime import datetime
    output_dir = Path("output/ai_summaries")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"summary_{timestamp}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# AI 每日摘要\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(summary)

    print(f"[OK] Summary saved to: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    summary = generate_ai_summary()

    if summary:
        print("\n" + "=" * 60)
        print("AI Summary Generated:")
        print("=" * 60)
        print(summary)
        print("=" * 60)

        # 保存到文件
        save_summary_to_file(summary)

        # 输出到 GitHub Actions 日志
        summary_file = save_summary_to_file(summary)
        if summary_file:
            # 设置环境变量供后续步骤使用
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"summary_file={summary_file}\n")

        sys.exit(0)
    else:
        print("[ERROR] Failed to generate AI summary")
        sys.exit(1)
