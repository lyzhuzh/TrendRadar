# coding=utf-8
"""
AI 总结集成示例 - 将此代码集成到 trendradar/__main__.py 的 _generate_ai_summary 方法中

在 _generate_ai_summary 方法中替换当前实现：
"""
def _generate_ai_summary(
    self,
    rss_items: Optional[List[Dict]] = None,
) -> Optional[str]:
    """
    生成 AI 总结

    Args:
        rss_items: RSS 条目列表（未使用，保留兼容性）

    Returns:
        AI 总结文本，如果未启用或失败则返回 None
    """
    ai_config = self.ctx.config.get("AI", {})
    summary_config = ai_config.get("SUMMARY", {})

    if not summary_config.get("ENABLED", False):
        return None

    provider = ai_config.get("PROVIDER", "openai")
    api_key = ai_config.get("API_KEY", "")
    base_url = ai_config.get("BASE_URL", "")
    model = ai_config.get("MODEL", "gpt-4")

    if not api_key:
        print("[WARNING] AI_API_KEY not configured, skipping AI summary")
        return None

    try:
        # 导入数据查询工具
        from mcp_server.tools.data_query import DataQueryTools
        from datetime import datetime

        # 获取今日新闻数据
        tools = DataQueryTools()
        result = tools.get_news_for_summary(
            mode=summary_config.get("MODE", "current"),
            group_by=summary_config.get("GROUP_BY", "keyword"),
            max_news_per_keyword=summary_config.get("MAX_NEWS_PER_KEYWORD", 10),
            include_url=summary_config.get("INCLUDE_URL", True)
        )

        if not result.get("success"):
            print(f"[WARNING] Failed to get summary data: {result.get('error', {}).get('message')}")
            return None

        # 构建 AI 提示
        summary_data = result.get("keyword_groups", [])
        prompt = self._build_summary_prompt(summary_data, summary_config)

        # 调用 AI API
        summary = self._call_ai_api(provider, api_key, base_url, model, prompt)

        if summary:
            print("[AI] Summary generated successfully")
            return summary
        else:
            print("[WARNING] AI API returned empty response")
            return None

    except Exception as e:
        print(f"[WARNING] AI summary generation failed: {e}")
        return None


def _build_summary_prompt(self, keyword_groups, summary_config):
    """构建 AI 提示词"""
    prompt_template = summary_config.get("PROMPT_TEMPLATE",
        "请根据以下热点新闻数据生成每日摘要。按关键词分组，每组用 1-2 句话总结，最后列出相关链接。")

    prompt = prompt_template + "\n\n"
    prompt += f"生成时间: {self.ctx.get_time().strftime('%Y-%m-%d %H:%M')}\n\n"

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

    return prompt


def _call_ai_api(self, provider, api_key, base_url, model, prompt):
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
            print(f"[ERROR] Unsupported AI provider: {provider}")
            return None

    except ImportError as e:
        print(f"[ERROR] Missing AI library: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] AI API call failed: {e}")
        return None
