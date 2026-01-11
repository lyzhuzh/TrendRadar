"""
数据查询工具

实现P0核心的数据查询工具。
"""

from typing import Dict, List, Optional, Union

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_date_range,
    validate_top_n,
    validate_mode,
    validate_date_query,
    normalize_date_range
)
from ..utils.errors import MCPError


class DataQueryTools:
    """数据查询工具类"""

    def __init__(self, project_root: str = None):
        """
        初始化数据查询工具

        Args:
            project_root: 项目根目录
        """
        self.data_service = DataService(project_root)

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        获取最新一批爬取的新闻数据

        Args:
            platforms: 平台ID列表，如 ['zhihu', 'weibo']
            limit: 返回条数限制，默认20
            include_url: 是否包含URL链接，默认False（节省token）

        Returns:
            新闻列表字典

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_latest_news(platforms=['zhihu'], limit=10)
            >>> print(result['total'])
            10
        """
        try:
            # 参数验证
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # 获取数据
            news_list = self.data_service.get_latest_news(
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "platforms": platforms,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Union[Dict, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        按关键词搜索历史新闻

        Args:
            keyword: 搜索关键词（必需）
            date_range: 日期范围，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            platforms: 平台过滤列表
            limit: 返回条数限制（可选，默认返回所有）

        Returns:
            搜索结果字典

        Example (假设今天是 2025-11-17):
            >>> tools = DataQueryTools()
            >>> result = tools.search_news_by_keyword(
            ...     keyword="人工智能",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"},
            ...     limit=50
            ... )
            >>> print(result['total'])
        """
        try:
            # 参数验证
            keyword = validate_keyword(keyword)
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)

            if limit is not None:
                limit = validate_limit(limit, default=100)

            # 搜索数据
            search_result = self.data_service.search_news_by_keyword(
                keyword=keyword,
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit
            )

            return {
                **search_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_trending_topics(
        self,
        top_n: Optional[int] = None,
        mode: Optional[str] = None,
        extract_mode: Optional[str] = None
    ) -> Dict:
        """
        获取热点话题统计

        Args:
            top_n: 返回TOP N话题，默认10
            mode: 时间模式
                - "daily": 当日累计数据统计
                - "current": 最新一批数据统计（默认）
            extract_mode: 提取模式
                - "keywords": 统计预设关注词（基于 config/frequency_words.txt，默认）
                - "auto_extract": 自动从新闻标题提取高频词

        Returns:
            话题频率统计字典

        Example:
            >>> tools = DataQueryTools()
            >>> # 使用预设关注词
            >>> result = tools.get_trending_topics(top_n=5, mode="current")
            >>> # 自动提取高频词
            >>> result = tools.get_trending_topics(top_n=10, extract_mode="auto_extract")
        """
        try:
            # 参数验证
            top_n = validate_top_n(top_n, default=10)
            valid_modes = ["daily", "current"]
            mode = validate_mode(mode, valid_modes, default="current")

            # 验证 extract_mode
            if extract_mode is None:
                extract_mode = "keywords"
            elif extract_mode not in ["keywords", "auto_extract"]:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"不支持的提取模式: {extract_mode}",
                        "suggestion": "支持的模式: keywords, auto_extract"
                    }
                }

            # 获取趋势话题
            trending_result = self.data_service.get_trending_topics(
                top_n=top_n,
                mode=mode,
                extract_mode=extract_mode
            )

            return {
                **trending_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_news_by_date(
        self,
        date_range: Optional[Union[Dict[str, str], str]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        按日期查询新闻，支持自然语言日期

        Args:
            date_range: 日期范围（可选，默认"今天"），支持：
                - 范围对象：{"start": "2025-01-01", "end": "2025-01-07"}
                - 相对日期：今天、昨天、前天、3天前
                - 单日字符串：2025-10-10
            platforms: 平台ID列表，如 ['zhihu', 'weibo']
            limit: 返回条数限制，默认50
            include_url: 是否包含URL链接，默认False（节省token）

        Returns:
            新闻列表字典

        Example:
            >>> tools = DataQueryTools()
            >>> # 不指定日期，默认查询今天
            >>> result = tools.get_news_by_date(platforms=['zhihu'], limit=20)
            >>> # 指定日期
            >>> result = tools.get_news_by_date(
            ...     date_range="昨天",
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
            >>> print(result['total'])
            20
        """
        try:
            # 参数验证 - 默认今天
            if date_range is None:
                date_range = "今天"

            # 规范化 date_range（处理 JSON 字符串序列化问题）
            date_range = normalize_date_range(date_range)

            # 处理 date_range：支持字符串或对象
            if isinstance(date_range, dict):
                # 范围对象，取 start 日期
                date_str = date_range.get('start', '今天')
            else:
                date_str = date_range
            target_date = validate_date_query(date_str)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # 获取数据
            news_list = self.data_service.get_news_by_date(
                target_date=target_date,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "date": target_date.strftime("%Y-%m-%d"),
                "date_range": date_range,
                "platforms": platforms,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    # ========================================
    # RSS 数据查询方法
    # ========================================

    def get_latest_rss(
        self,
        feeds: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_summary: bool = False
    ) -> Dict:
        """
        获取最新的 RSS 数据

        Args:
            feeds: RSS 源 ID 列表，如 ['hacker-news', '36kr']
            limit: 返回条数限制，默认50
            include_summary: 是否包含摘要，默认False（节省token）

        Returns:
            RSS 条目列表字典
        """
        try:
            limit = validate_limit(limit, default=50)

            rss_list = self.data_service.get_latest_rss(
                feeds=feeds,
                limit=limit,
                include_summary=include_summary
            )

            return {
                "rss": rss_list,
                "total": len(rss_list),
                "feeds": feeds,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def search_rss(
        self,
        keyword: str,
        feeds: Optional[List[str]] = None,
        days: int = 7,
        limit: Optional[int] = None,
        include_summary: bool = False
    ) -> Dict:
        """
        搜索 RSS 数据

        Args:
            keyword: 搜索关键词
            feeds: RSS 源 ID 列表
            days: 搜索最近 N 天的数据，默认 7 天
            limit: 返回条数限制，默认50
            include_summary: 是否包含摘要

        Returns:
            匹配的 RSS 条目列表
        """
        try:
            keyword = validate_keyword(keyword)
            limit = validate_limit(limit, default=50)

            if days < 1 or days > 30:
                days = 7

            rss_list = self.data_service.search_rss(
                keyword=keyword,
                feeds=feeds,
                days=days,
                limit=limit,
                include_summary=include_summary
            )

            return {
                "rss": rss_list,
                "total": len(rss_list),
                "keyword": keyword,
                "feeds": feeds,
                "days": days,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_rss_feeds_status(self) -> Dict:
        """
        获取 RSS 源状态

        Returns:
            RSS 源状态信息
        """
        try:
            status = self.data_service.get_rss_feeds_status()

            return {
                **status,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_news_for_summary(
        self,
        date_range: Optional[Union[Dict, str]] = None,
        mode: str = "daily",
        group_by: str = "keyword",
        max_news_per_keyword: int = 10,
        include_url: bool = False
    ) -> Dict:
        """
        获取按关键词分组的新闻数据，用于 AI 生成每日摘要

        Args:
            date_range: 日期范围（可选，默认"今天"）
            mode: 报告模式 ("daily"|"current"|"incremental")
            group_by: 分组方式 ("keyword"=按关键词, "platform"=按平台)
            max_news_per_keyword: 每个关键词最多返回新闻数，默认10
            include_url: 是否包含URL链接，默认False（节省token）

        Returns:
            按关键词分组的新闻数据字典

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_news_for_summary(
            ...     mode="daily",
            ...     group_by="keyword",
            ...     include_url=True
            ... )
            >>> print(result['total_keywords'])
        """
        import traceback
        import sys

        try:
            from datetime import datetime

            # 参数验证
            valid_modes = ["daily", "current", "incremental"]
            mode = validate_mode(mode, valid_modes, default="daily")

            if group_by not in ["keyword", "platform"]:
                group_by = "keyword"

            if not isinstance(max_news_per_keyword, int) or max_news_per_keyword < 1:
                max_news_per_keyword = 10

            # 处理 date_range：默认今天
            if date_range is None:
                date_range = "今天"

            # 确保 date_range 是字符串
            if not isinstance(date_range, str):
                date_range = str(date_range)

            # 规范化 date_range
            normalized_range = normalize_date_range(date_range)

            # 处理 date_range：支持字符串或对象
            if isinstance(normalized_range, dict):
                date_str = normalized_range.get('start', '今天')
            else:
                date_str = normalized_range if isinstance(normalized_range, str) else "今天"

            target_date = validate_date_query(date_str)

            # 读取数据
            all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                date=target_date,
                platform_ids=None
            )

            if not all_titles:
                return {
                    "success": False,
                    "error": {
                        "code": "DATA_NOT_FOUND",
                        "message": f"未找到 {date_str} 的新闻数据",
                        "suggestion": "请确保爬虫已经运行并生成了数据"
                    }
                }

            # 读取关键词配置
            word_groups = self.data_service.parser.parse_frequency_words()

            # 构建关键词到新闻的映射
            keyword_to_news = {}
            platform_to_news = {}

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    rank = info["ranks"][0] if info["ranks"] else 0
                    is_new = len(info.get("ranks", [])) == 1  # 只出现一次视为新增

                    news_item = {
                        "title": title,
                        "source_name": platform_name,
                        "rank": rank,
                        "is_new": is_new
                    }

                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobile_url"] = info.get("mobileUrl", "")

                    # 按平台分组
                    if platform_id not in platform_to_news:
                        platform_to_news[platform_id] = []
                    platform_to_news[platform_id].append(news_item)

                    # 按关键词分组
                    for group in word_groups:
                        all_words = []
                        # 提取 required 词
                        for word_dict in group.get("required", []):
                            if isinstance(word_dict, dict):
                                all_words.append(word_dict.get("word", ""))
                            elif isinstance(word_dict, str):
                                all_words.append(word_dict)
                        # 提取 normal 词
                        for word_dict in group.get("normal", []):
                            if isinstance(word_dict, dict):
                                all_words.append(word_dict.get("word", ""))
                            elif isinstance(word_dict, str):
                                all_words.append(word_dict)

                        for word in all_words:
                            if word and word in title:
                                if word not in keyword_to_news:
                                    keyword_to_news[word] = []
                                keyword_to_news[word].append(news_item)

            # 按 group_by 组织结果
            if group_by == "keyword":
                groups = []
                for keyword, news_list in sorted(keyword_to_news.items(),
                                                   key=lambda x: len(x[1]),
                                                   reverse=True):
                    # 按排名排序，限制数量
                    news_list.sort(key=lambda x: x["rank"])
                    limited_news = news_list[:max_news_per_keyword]

                    groups.append({
                        "keyword": keyword,
                        "count": len(news_list),
                        "news": limited_news
                    })

                return {
                    "success": True,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "mode": mode,
                    "group_by": group_by,
                    "total_keywords": len(groups),
                    "total_news": sum(g["count"] for g in groups),
                    "keyword_groups": groups
                }

            else:  # group_by == "platform"
                groups = []
                for platform_id, news_list in sorted(platform_to_news.items(),
                                                      key=lambda x: len(x[1]),
                                                      reverse=True):
                    # 按排名排序，限制数量
                    news_list.sort(key=lambda x: x["rank"])
                    limited_news = news_list[:max_news_per_keyword]

                    groups.append({
                        "platform": platform_id,
                        "platform_name": id_to_name.get(platform_id, platform_id),
                        "count": len(news_list),
                        "news": limited_news
                    })

                return {
                    "success": True,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "mode": mode,
                    "group_by": group_by,
                    "total_platforms": len(groups),
                    "total_news": sum(g["count"] for g in groups),
                    "platform_groups": groups
                }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

