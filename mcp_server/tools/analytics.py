"""
高级dataanalysis工具

提供热度趋势analysis、Platform对比、关键词共现、情感analysis等高级analysis功能。
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from difflib import SequenceMatcher

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_top_n,
    validate_date_range
)
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


def calculate_news_weight(news_data: Dict, rank_threshold: int = 5) -> float:
    """
    计算news权重（用于sort）

    基于 main.py 的权重算法实现，综合考虑：
    - rank权重 (60%)：news在榜单中的rank
    - 频次权重 (30%)：news出现的次数
    - 热度权重 (10%)：高rank出现的比例

    Args:
        news_data: newsdatadictionary，include ranks 和 count 字段
        rank_threshold: 高rank阈值，default5

    Returns:
        权重分数（0-100之间的浮点数）
    """
    ranks = news_data.get("ranks", [])
    if not ranks:
        return 0.0

    count = news_data.get("count", len(ranks))

    # 权重配置（与 config.yaml 保持一致）
    RANK_WEIGHT = 0.6
    FREQUENCY_WEIGHT = 0.3
    HOTNESS_WEIGHT = 0.1

    # 1. rank权重：Σ(11 - min(rank, 10)) / 出现次数
    rank_scores = []
    for rank in ranks:
        score = 11 - min(rank, 10)
        rank_scores.append(score)

    rank_weight = sum(rank_scores) / len(ranks) if ranks else 0

    # 2. 频次权重：min(出现次数, 10) × 10
    frequency_weight = min(count, 10) * 10

    # 3. 热度加成：高rank次数 / 总出现次数 × 100
    high_rank_count = sum(1 for rank in ranks if rank <= rank_threshold)
    hotness_ratio = high_rank_count / len(ranks) if ranks else 0
    hotness_weight = hotness_ratio * 100

    # 综合权重
    total_weight = (
        rank_weight * RANK_WEIGHT
        + frequency_weight * FREQUENCY_WEIGHT
        + hotness_weight * HOTNESS_WEIGHT
    )

    return total_weight


class AnalyticsTools:
    """高级dataanalysis工具类"""

    def __init__(self, project_root: str = None):
        """
        Initializeanalysis工具

        Args:
            project_root: 项目根directory
        """
        self.data_service = DataService(project_root)

    def analyze_data_insights_unified(
        self,
        insight_type: str = "platform_compare",
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        统一data洞察analysis工具 - 整合多种dataanalysis模式

        Args:
            insight_type: 洞察类型，optional值：
                - "platform_compare": Platform对比analysis（对比不同Platform对话题的关注度）
                - "platform_activity": Platform活跃度statistics（statistics各Platform发布频率和活跃time）
                - "keyword_cooccur": 关键词共现analysis（analysis关键词同时出现的模式）
            topic: 话题关键词（optional，platform_compare模式适用）
            date_range: date范围，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            min_frequency: 最小共现频次（keyword_cooccur模式），default3
            top_n: returnTOP Nresult（keyword_cooccur模式），default20

        Returns:
            data洞察analysisresultdictionary

        Examples:
            - analyze_data_insights_unified(insight_type="platform_compare", topic="人工智能")
            - analyze_data_insights_unified(insight_type="platform_activity", date_range={...})
            - analyze_data_insights_unified(insight_type="keyword_cooccur", min_frequency=5)
        """
        try:
            # 参数Validate
            if insight_type not in ["platform_compare", "platform_activity", "keyword_cooccur"]:
                raise InvalidParameterError(
                    f"无效的洞察类型: {insight_type}",
                    suggestion="support的类型: platform_compare, platform_activity, keyword_cooccur"
                )

            # 根据洞察类型调用相应方法
            if insight_type == "platform_compare":
                return self.compare_platforms(
                    topic=topic,
                    date_range=date_range
                )
            elif insight_type == "platform_activity":
                return self.get_platform_activity_stats(
                    date_range=date_range
                )
            else:  # keyword_cooccur
                return self.analyze_keyword_cooccurrence(
                    min_frequency=min_frequency,
                    top_n=top_n
                )

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

    def analyze_topic_trend_unified(
        self,
        topic: str,
        analysis_type: str = "trend",
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day",
        threshold: float = 3.0,
        time_window: int = 24,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        统一话题趋势analysis工具 - 整合多种趋势analysis模式

        Args:
            topic: 话题关键词（必需）
            analysis_type: analysis类型，optional值：
                - "trend": 热度趋势analysis（追踪话题的热度变化）
                - "lifecycle": 生命周期analysis（从出现到消失的完整周期）
                - "viral": abnormal热度检测（识别突然爆火的话题）
                - "predict": 话题预测（预测未来可能的hot topic）
            date_range: date范围（trend和lifecycle模式），optional
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **default**: When not specifieddefaultanalysis最近7天
            granularity: time粒度（trend模式），default"day"（hour/day）
            threshold: 热度突增倍数阈值（viral模式），default3.0
            time_window: 检测time窗口hour数（viral模式），default24
            lookahead_hours: 预测未来hour数（predict模式），default6
            confidence_threshold: 置信度阈值（predict模式），default0.7

        Returns:
            趋势analysisresultdictionary

        Examples:
            - analyze_topic_trend_unified(topic="人工智能", analysis_type="trend", date_range={"start": "2025-10-18", "end": "2025-10-25"})
            - analyze_topic_trend_unified(topic="特斯拉", analysis_type="lifecycle", date_range={"start": "2025-10-18", "end": "2025-10-25"})
            - analyze_topic_trend_unified(topic="比特币", analysis_type="viral", threshold=3.0)
            - analyze_topic_trend_unified(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
        """
        try:
            # 参数Validate
            topic = validate_keyword(topic)

            if analysis_type not in ["trend", "lifecycle", "viral", "predict"]:
                raise InvalidParameterError(
                    f"无效的analysis类型: {analysis_type}",
                    suggestion="support的类型: trend, lifecycle, viral, predict"
                )

            # 根据analysis类型调用相应方法
            if analysis_type == "trend":
                return self.get_topic_trend_analysis(
                    topic=topic,
                    date_range=date_range,
                    granularity=granularity
                )
            elif analysis_type == "lifecycle":
                return self.analyze_topic_lifecycle(
                    topic=topic,
                    date_range=date_range
                )
            elif analysis_type == "viral":
                # viral模式不needtopic参数，use通用检测
                return self.detect_viral_topics(
                    threshold=threshold,
                    time_window=time_window
                )
            else:  # predict
                # predict模式不needtopic参数，use通用预测
                return self.predict_trending_topics(
                    lookahead_hours=lookahead_hours,
                    confidence_threshold=confidence_threshold
                )

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

    def get_topic_trend_analysis(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day"
    ) -> Dict:
        """
        热度趋势analysis - 追踪特定话题的热度变化趋势

        Args:
            topic: 话题关键词
            date_range: date范围（optional）
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **default**: When not specifieddefaultanalysis最近7天
            granularity: time粒度，仅support day（天）

        Returns:
            趋势analysisresultdictionary

        Examples:
            用户询问示例：
            - "帮我analysis一下'人工智能'这个话题最近一周的热度趋势"
            - "查看'比特币'过去一周的热度变化"
            - "看看'iPhone'最近7天的趋势如何"
            - "analysis'特斯拉'最近一个月的热度趋势"
            - "查看'ChatGPT'2024年12月的趋势变化"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> # analysis7天趋势
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="人工智能",
            ...     date_range={"start": "2025-10-18", "end": "2025-10-25"},
            ...     granularity="day"
            ... )
            >>> # analysishistory月份趋势
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="特斯拉",
            ...     date_range={"start": "2024-12-01", "end": "2024-12-31"},
            ...     granularity="day"
            ... )
            >>> print(result['trend_data'])
        """
        try:
            # Validate参数
            topic = validate_keyword(topic)

            # Validate粒度参数（只supportday）
            if granularity != "day":
                from ..utils.errors import InvalidParameterError
                raise InvalidParameterError(
                    f"不support的粒度参数: {granularity}",
                    suggestion="current仅support 'day' 粒度，因为底层data按天聚合"
                )

            # Processdate范围（When not specifieddefault最近7天）
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # default最近7天
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # 收集趋势data
            trend_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # statistics该time点的话题出现次数
                    count = 0
                    matched_titles = []

                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1
                                matched_titles.append(title)

                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count,
                        "sample_titles": matched_titles[:3]  # 只保留前3个样本
                    })

                except DataNotFoundError:
                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0,
                        "sample_titles": []
                    })

                # 按天增加time
                current_date += timedelta(days=1)

            # 计算趋势指标
            counts = [item["count"] for item in trend_data]
            total_days = (end_date - start_date).days + 1

            if len(counts) >= 2:
                # 计算涨跌幅度
                first_non_zero = next((c for c in counts if c > 0), 0)
                last_count = counts[-1]

                if first_non_zero > 0:
                    change_rate = ((last_count - first_non_zero) / first_non_zero) * 100
                else:
                    change_rate = 0

                # 找到峰值time
                max_count = max(counts)
                peak_index = counts.index(max_count)
                peak_time = trend_data[peak_index]["date"]
            else:
                change_rate = 0
                peak_time = None
                max_count = 0

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "granularity": granularity,
                "trend_data": trend_data,
                "statistics": {
                    "total_mentions": sum(counts),
                    "average_mentions": round(sum(counts) / len(counts), 2) if counts else 0,
                    "peak_count": max_count,
                    "peak_time": peak_time,
                    "change_rate": round(change_rate, 2)
                },
                "trend_direction": "上升" if change_rate > 10 else "下降" if change_rate < -10 else "稳定"
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

    def compare_platforms(
        self,
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Platform对比analysis - 对比不同Platform对同一话题的关注度

        Args:
            topic: 话题关键词（optional，不指定则对比整体活跃度）
            date_range: date范围，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

        Returns:
            Platform对比analysisresult

        Examples:
            用户询问示例：
            - "对比一下各个Platform对'人工智能'话题的关注度"
            - "看看Zhihu和Weibo哪个Platform更关注科技news"
            - "analysis各Platformtoday的hot topic分布"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.compare_platforms(
            ...     topic="人工智能",
            ...     date_range={"start": "2025-10-01", "end": "2025-10-11"}
            ... )
            >>> print(result['platform_stats'])
        """
        try:
            # 参数Validate
            if topic:
                topic = validate_keyword(topic)
            date_range_tuple = validate_date_range(date_range)

            # 确定date范围
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # 收集各Platformdata
            platform_stats = defaultdict(lambda: {
                "total_news": 0,
                "topic_mentions": 0,
                "unique_titles": set(),
                "top_keywords": Counter()
            })

            # 遍历date范围
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title in titles.keys():
                            platform_stats[platform_name]["total_news"] += 1
                            platform_stats[platform_name]["unique_titles"].add(title)

                            # 如果指定了话题，statisticsinclude话题的news
                            if topic and topic.lower() in title.lower():
                                platform_stats[platform_name]["topic_mentions"] += 1

                            # 提取关键词（简单分词）
                            keywords = self._extract_keywords(title)
                            platform_stats[platform_name]["top_keywords"].update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 转换为可序列化的格式
            result_stats = {}
            for platform, stats in platform_stats.items():
                coverage_rate = 0
                if stats["total_news"] > 0:
                    coverage_rate = (stats["topic_mentions"] / stats["total_news"]) * 100

                result_stats[platform] = {
                    "total_news": stats["total_news"],
                    "topic_mentions": stats["topic_mentions"],
                    "unique_titles": len(stats["unique_titles"]),
                    "coverage_rate": round(coverage_rate, 2),
                    "top_keywords": [
                        {"keyword": k, "count": v}
                        for k, v in stats["top_keywords"].most_common(5)
                    ]
                }

            # 找出各Platform独有的hot topic
            unique_topics = self._find_unique_topics(platform_stats)

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_stats": result_stats,
                "unique_topics": unique_topics,
                "total_platforms": len(result_stats)
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

    def analyze_keyword_cooccurrence(
        self,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        关键词共现analysis - analysis哪些关键词经常同时出现

        Args:
            min_frequency: 最小共现频次
            top_n: returnTOP N关键词对

        Returns:
            关键词共现analysisresult

        Examples:
            用户询问示例：
            - "analysis一下哪些关键词经常一起出现"
            - "看看'人工智能'经常和哪些词一起出现"
            - "找出todaynews中的关键词关联"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.analyze_keyword_cooccurrence(
            ...     min_frequency=5,
            ...     top_n=15
            ... )
            >>> print(result['cooccurrence_pairs'])
        """
        try:
            # 参数Validate
            min_frequency = validate_limit(min_frequency, default=3, max_limit=100)
            top_n = validate_top_n(top_n, default=20)

            # 读取today的data
            all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # 关键词共现statistics
            cooccurrence = Counter()
            keyword_titles = defaultdict(list)

            for platform_id, titles in all_titles.items():
                for title in titles.keys():
                    # 提取关键词
                    keywords = self._extract_keywords(title)

                    # record每个关键词出现的title
                    for kw in keywords:
                        keyword_titles[kw].append(title)

                    # 计算两两共现
                    if len(keywords) >= 2:
                        for i, kw1 in enumerate(keywords):
                            for kw2 in keywords[i+1:]:
                                # 统一sort，避免重复
                                pair = tuple(sorted([kw1, kw2]))
                                cooccurrence[pair] += 1

            # 过滤低频共现
            filtered_pairs = [
                (pair, count) for pair, count in cooccurrence.items()
                if count >= min_frequency
            ]

            # sort并取TOP N
            top_pairs = sorted(filtered_pairs, key=lambda x: x[1], reverse=True)[:top_n]

            # 构建result
            result_pairs = []
            for (kw1, kw2), count in top_pairs:
                # 找出同时include两个关键词的title样本
                titles_with_both = [
                    title for title in keyword_titles[kw1]
                    if kw2 in self._extract_keywords(title)
                ]

                result_pairs.append({
                    "keyword1": kw1,
                    "keyword2": kw2,
                    "cooccurrence_count": count,
                    "sample_titles": titles_with_both[:3]
                })

            return {
                "success": True,
                "cooccurrence_pairs": result_pairs,
                "total_pairs": len(result_pairs),
                "min_frequency": min_frequency,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def analyze_sentiment(
        self,
        topic: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 50,
        sort_by_weight: bool = True,
        include_url: bool = False
    ) -> Dict:
        """
        情感倾向analysis - Generate用于 AI 情感analysis的结构化hint词

        本工具收集newsdata并Generate优化的 AI hint词，你can将其Send给 AI 进行深度情感analysis。

        Args:
            topic: 话题关键词（optional），只analysisinclude该关键词的news
            platforms: Platform过滤list（optional），如 ['zhihu', 'weibo']
            date_range: date范围（optional），格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       不指定则defaultquerytoday的data
            limit: returnnews数量limit，default50，最大100
            sort_by_weight: 是否按权重sort，defaultTrue（推荐）
            include_url: 是否includeURLlink，defaultFalse（节省token）

        Returns:
            include AI hint词和newsdata的结构化result

        Examples:
            用户询问示例：
            - "analysis一下todaynews的情感倾向"
            - "看看'特斯拉'相关news是正面还是负面的"
            - "analysis各Platform对'人工智能'的情感态度"
            - "看看'特斯拉'相关news是正面还是负面的，请选择一周内的前10条news来analysis"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> # analysistoday的特斯拉news，return前10条
            >>> result = tools.analyze_sentiment(
            ...     topic="特斯拉",
            ...     limit=10
            ... )
            >>> # analysis一周内的特斯拉news，return前10条按权重sort
            >>> result = tools.analyze_sentiment(
            ...     topic="特斯拉",
            ...     date_range={"start": "2025-10-06", "end": "2025-10-13"},
            ...     limit=10
            ... )
            >>> print(result['ai_prompt'])  # GetGenerate的hint词
        """
        try:
            # 参数Validate
            if topic:
                topic = validate_keyword(topic)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Processdate范围
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # defaulttoday
                start_date = end_date = datetime.now()

            # 收集newsdata（support多天）
            all_news_items = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # 收集该date的news
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        for title, info in titles.items():
                            # 如果指定了话题，只收集include话题的title
                            if topic and topic.lower() not in title.lower():
                                continue

                            news_item = {
                                "platform": platform_name,
                                "title": title,
                                "ranks": info.get("ranks", []),
                                "count": len(info.get("ranks", [])),
                                "date": current_date.strftime("%Y-%m-%d")
                            }

                            # 条件性添加 URL 字段
                            if include_url:
                                news_item["url"] = info.get("url", "")
                                news_item["mobileUrl"] = info.get("mobileUrl", "")

                            all_news_items.append(news_item)

                except DataNotFoundError:
                    # 该date没有data，继续下一天
                    pass

                # 下一天
                current_date += timedelta(days=1)

            if not all_news_items:
                time_desc = "today" if start_date == end_date else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"未找到相关news（{time_desc}）",
                    suggestion="请尝试其他话题、date范围或Platform"
                )

            # 去重（同一title只保留一次）
            unique_news = {}
            for item in all_news_items:
                key = f"{item['platform']}::{item['title']}"
                if key not in unique_news:
                    unique_news[key] = item
                else:
                    # 合并 ranks（如果同一news在多天出现）
                    existing = unique_news[key]
                    existing["ranks"].extend(item["ranks"])
                    existing["count"] = len(existing["ranks"])

            deduplicated_news = list(unique_news.values())

            # 按权重sort（如果enabled）
            if sort_by_weight:
                deduplicated_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )

            # limitreturn数量
            selected_news = deduplicated_news[:limit]

            # Generate AI hint词
            ai_prompt = self._create_sentiment_analysis_prompt(
                news_data=selected_news,
                topic=topic
            )

            # 构建time范围描述
            if start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "method": "ai_prompt_generation",
                "summary": {
                    "total_found": len(deduplicated_news),
                    "returned_count": len(selected_news),
                    "requested_limit": limit,
                    "duplicates_removed": len(all_news_items) - len(deduplicated_news),
                    "topic": topic,
                    "time_range": time_range_desc,
                    "platforms": list(set(item["platform"] for item in selected_news)),
                    "sorted_by_weight": sort_by_weight
                },
                "ai_prompt": ai_prompt,
                "news_sample": selected_news,
                "usage_note": "请将 ai_prompt 字段的contentSend给 AI 进行情感analysis"
            }

            # 如果return数量少于请求数量，增加hint
            if len(selected_news) < limit and len(deduplicated_news) >= limit:
                result["note"] = "return数量少于请求数量是因为去重逻辑（同一title在不同Platform只保留一次）"
            elif len(deduplicated_news) < limit:
                result["note"] = f"在指定time范围内仅找到 {len(deduplicated_news)} 条匹配的news"

            return result

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

    def _create_sentiment_analysis_prompt(
        self,
        news_data: List[Dict],
        topic: Optional[str]
    ) -> str:
        """
        Create情感analysis的 AI hint词

        Args:
            news_data: newsdatalist（已sort和Limit quantity）
            topic: 话题关键词

        Returns:
            格式化的 AI hint词
        """
        # 按Platform分组
        platform_news = defaultdict(list)
        for item in news_data:
            platform_news[item["platform"]].append({
                "title": item["title"],
                "date": item.get("date", "")
            })

        # 构建hint词
        prompt_parts = []

        # 1. 任务说明
        if topic:
            prompt_parts.append(f"请analysis以下关于「{topic}」的newstitle的情感倾向。")
        else:
            prompt_parts.append("请analysis以下newstitle的情感倾向。")

        prompt_parts.append("")
        prompt_parts.append("analysis要求：")
        prompt_parts.append("1. 识别每条news的情感倾向（正面/负面/中性）")
        prompt_parts.append("2. statistics各情感类别的数量和百分比")
        prompt_parts.append("3. analysis不同Platform的情感差异")
        prompt_parts.append("4. 总结整体情感趋势")
        prompt_parts.append("5. 列举典型的正面和负面news样本")
        prompt_parts.append("")

        # 2. data概览
        prompt_parts.append(f"data概览：")
        prompt_parts.append(f"- 总news数：{len(news_data)}")
        prompt_parts.append(f"- 覆盖Platform：{len(platform_news)}")

        # time范围
        dates = set(item.get("date", "") for item in news_data if item.get("date"))
        if dates:
            date_list = sorted(dates)
            if len(date_list) == 1:
                prompt_parts.append(f"- time范围：{date_list[0]}")
            else:
                prompt_parts.append(f"- time范围：{date_list[0]} to {date_list[-1]}")

        prompt_parts.append("")

        # 3. 按Platform展示news
        prompt_parts.append("newslist（按Platform分类，已按Important性sort）：")
        prompt_parts.append("")

        for platform, items in sorted(platform_news.items()):
            prompt_parts.append(f"【{platform}】({len(items)} 条)")
            for i, item in enumerate(items, 1):
                title = item["title"]
                date_str = f" [{item['date']}]" if item.get("date") else ""
                prompt_parts.append(f"{i}. {title}{date_str}")
            prompt_parts.append("")

        # 4. output格式说明
        prompt_parts.append("请按以下格式outputanalysisresult：")
        prompt_parts.append("")
        prompt_parts.append("## 情感分布statistics")
        prompt_parts.append("- 正面：XX条 (XX%)")
        prompt_parts.append("- 负面：XX条 (XX%)")
        prompt_parts.append("- 中性：XX条 (XX%)")
        prompt_parts.append("")
        prompt_parts.append("## Platform情感对比")
        prompt_parts.append("[各Platform的情感倾向差异]")
        prompt_parts.append("")
        prompt_parts.append("## 整体情感趋势")
        prompt_parts.append("[总体analysis和关键发现]")
        prompt_parts.append("")
        prompt_parts.append("## 典型样本")
        prompt_parts.append("正面news样本：")
        prompt_parts.append("[列举3-5条]")
        prompt_parts.append("")
        prompt_parts.append("负面news样本：")
        prompt_parts.append("[列举3-5条]")

        return "\n".join(prompt_parts)

    def find_similar_news(
        self,
        reference_title: str,
        threshold: float = 0.6,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        相似news查找 - 基于title相似度查找相关news

        Args:
            reference_title: 参考title
            threshold: 相似度阈值（0-1之间）
            limit: return条数limit，default50
            include_url: 是否includeURLlink，defaultFalse（节省token）

        Returns:
            相似newslist

        Examples:
            用户询问示例：
            - "找出和'特斯拉降价'相似的news"
            - "查找关于iPhone发布的类似报道"
            - "看看有没有和这条news相似的报道"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.find_similar_news(
            ...     reference_title="特斯拉宣布降价",
            ...     threshold=0.6,
            ...     limit=10
            ... )
            >>> print(result['similar_news'])
        """
        try:
            # 参数Validate
            reference_title = validate_keyword(reference_title)

            if not 0 <= threshold <= 1:
                raise InvalidParameterError(
                    "threshold 必须在 0 到 1 之间",
                    suggestion="推荐值：0.5-0.8"
                )

            limit = validate_limit(limit, default=50)

            # 读取data
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # 计算相似度
            similar_items = []

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if title == reference_title:
                        continue

                    # 计算相似度
                    similarity = self._calculate_similarity(reference_title, title)

                    if similarity >= threshold:
                        news_item = {
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "similarity": round(similarity, 3),
                            "rank": info["ranks"][0] if info["ranks"] else 0
                        }

                        # 条件性添加 URL 字段
                        if include_url:
                            news_item["url"] = info.get("url", "")

                        similar_items.append(news_item)

            # 按相似度sort
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)

            # Limit quantity
            result_items = similar_items[:limit]

            if not result_items:
                raise DataNotFoundError(
                    f"未找到相似度exceed {threshold} 的news",
                    suggestion="请降低相似度阈值或尝试其他title"
                )

            result = {
                "success": True,
                "summary": {
                    "total_found": len(similar_items),
                    "returned_count": len(result_items),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_title": reference_title
                },
                "similar_news": result_items
            }

            if len(similar_items) < limit:
                result["note"] = f"相似度阈值 {threshold} 下仅找到 {len(similar_items)} 条相似news"

            return result

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

    def search_by_entity(
        self,
        entity: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
        sort_by_weight: bool = True
    ) -> Dict:
        """
        实体识别search - searchinclude特定人物/地点/机构的news

        Args:
            entity: 实体名称
            entity_type: 实体类型（person/location/organization），optional
            limit: return条数limit，default50，最大200
            sort_by_weight: 是否按权重sort，defaultTrue

        Returns:
            实体相关newslist

        Examples:
            用户询问示例：
            - "search马斯克相关的news"
            - "查找关于特斯拉公司的报道，return前20条"
            - "看看北京有什么news"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.search_by_entity(
            ...     entity="马斯克",
            ...     entity_type="person",
            ...     limit=20
            ... )
            >>> print(result['related_news'])
        """
        try:
            # 参数Validate
            entity = validate_keyword(entity)
            limit = validate_limit(limit, default=50)

            if entity_type and entity_type not in ["person", "location", "organization"]:
                raise InvalidParameterError(
                    f"无效的实体类型: {entity_type}",
                    suggestion="support的类型: person, location, organization"
                )

            # 读取data
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # searchinclude实体的news
            related_news = []
            entity_context = Counter()  # statistics实体周边的词

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if entity in title:
                        url = info.get("url", "")
                        mobile_url = info.get("mobileUrl", "")
                        ranks = info.get("ranks", [])
                        count = len(ranks)

                        related_news.append({
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "url": url,
                            "mobileUrl": mobile_url,
                            "ranks": ranks,
                            "count": count,
                            "rank": ranks[0] if ranks else 999
                        })

                        # 提取实体周边的关键词
                        keywords = self._extract_keywords(title)
                        entity_context.update(keywords)

            if not related_news:
                raise DataNotFoundError(
                    f"未找到include实体 '{entity}' 的news",
                    suggestion="请尝试其他实体名称"
                )

            # 移除实体本身
            if entity in entity_context:
                del entity_context[entity]

            # 按权重sort（如果enabled）
            if sort_by_weight:
                related_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )
            else:
                # 按ranksort
                related_news.sort(key=lambda x: x["rank"])

            # limitreturn数量
            result_news = related_news[:limit]

            return {
                "success": True,
                "entity": entity,
                "entity_type": entity_type or "auto",
                "related_news": result_news,
                "total_found": len(related_news),
                "returned_count": len(result_news),
                "sorted_by_weight": sort_by_weight,
                "related_keywords": [
                    {"keyword": k, "count": v}
                    for k, v in entity_context.most_common(10)
                ]
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

    def generate_summary_report(
        self,
        report_type: str = "daily",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        每日/每周摘要Generate器 - 自动Generatehot topic摘要report

        Args:
            report_type: report类型（daily/weekly）
            date_range: customdate范围（optional）

        Returns:
            Markdown格式的摘要report

        Examples:
            用户询问示例：
            - "Generatetoday的news摘要report"
            - "给我一份本周的hot topic总结"
            - "Generate过去7天的newsanalysisreport"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.generate_summary_report(
            ...     report_type="daily"
            ... )
            >>> print(result['markdown_report'])
        """
        try:
            # 参数Validate
            if report_type not in ["daily", "weekly"]:
                raise InvalidParameterError(
                    f"无效的report类型: {report_type}",
                    suggestion="support的类型: daily, weekly"
                )

            # 确定date范围
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                if report_type == "daily":
                    start_date = end_date = datetime.now()
                else:  # weekly
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=6)

            # 收集data
            all_keywords = Counter()
            all_platforms_news = defaultdict(int)
            all_titles_list = []

            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        all_platforms_news[platform_name] += len(titles)

                        for title in titles.keys():
                            all_titles_list.append({
                                "title": title,
                                "platform": platform_name,
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            # 提取关键词
                            keywords = self._extract_keywords(title)
                            all_keywords.update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Generatereport
            report_title = f"{'每日' if report_type == 'daily' else '每周'}newshot topic摘要"
            date_str = f"{start_date.strftime('%Y-%m-%d')}" if report_type == "daily" else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            # 构建Markdownreport
            markdown = f"""# {report_title}

**reportdate**: {date_str}
**Generatetime**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 data概览

- **总news数**: {len(all_titles_list)}
- **覆盖Platform**: {len(all_platforms_news)}
- **热门关键词数**: {len(all_keywords)}

## 🔥 TOP 10 热门话题

"""

            # 添加TOP 10关键词
            for i, (keyword, count) in enumerate(all_keywords.most_common(10), 1):
                markdown += f"{i}. **{keyword}** - 出现 {count} 次\n"

            # Platformanalysis
            markdown += "\n## 📱 Platform活跃度\n\n"
            sorted_platforms = sorted(all_platforms_news.items(), key=lambda x: x[1], reverse=True)

            for platform, count in sorted_platforms:
                markdown += f"- **{platform}**: {count} 条news\n"

            # 趋势变化（如果是周报）
            if report_type == "weekly":
                markdown += "\n## 📈 趋势analysis\n\n"
                markdown += "本周热度持续的话题（样本data）：\n\n"

                # 简单的趋势analysis
                top_keywords = [kw for kw, _ in all_keywords.most_common(5)]
                for keyword in top_keywords:
                    markdown += f"- **{keyword}**: 持续热门\n"

            # 添加样本news（按权重选择，确保确定性）
            markdown += "\n## 📰 精选news样本\n\n"

            # 确定性选取：按title的权重sort，取前5条
            # 这样相同input总是return相同result
            if all_titles_list:
                # 计算每条news的权重分数（基于关键词出现次数）
                news_with_scores = []
                for news in all_titles_list:
                    # 简单权重：statisticsincludeTOP关键词的次数
                    score = 0
                    title_lower = news['title'].lower()
                    for keyword, count in all_keywords.most_common(10):
                        if keyword.lower() in title_lower:
                            score += count
                    news_with_scores.append((news, score))

                # 按权重降序sort，权重相同则按title字母顺序（确保确定性）
                news_with_scores.sort(key=lambda x: (-x[1], x[0]['title']))

                # 取前5条
                sample_news = [item[0] for item in news_with_scores[:5]]

                for news in sample_news:
                    markdown += f"- [{news['platform']}] {news['title']}\n"

            markdown += "\n---\n\n*本report由 TrendRadar MCP 自动Generate*\n"

            return {
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "markdown_report": markdown,
                "statistics": {
                    "total_news": len(all_titles_list),
                    "platforms_count": len(all_platforms_news),
                    "keywords_count": len(all_keywords),
                    "top_keyword": all_keywords.most_common(1)[0] if all_keywords else None
                }
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

    def get_platform_activity_stats(
        self,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Platform活跃度statistics - statistics各Platform的发布频率和活跃time段

        Args:
            date_range: date范围（optional）

        Returns:
            Platform活跃度statisticsresult

        Examples:
            用户询问示例：
            - "statistics各Platformtoday的活跃度"
            - "看看哪个PlatformUpdate最频繁"
            - "analysis各Platform的发布time规律"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.get_platform_activity_stats(
            ...     date_range={"start": "2025-10-01", "end": "2025-10-11"}
            ... )
            >>> print(result['platform_activity'])
        """
        try:
            # 参数Validate
            date_range_tuple = validate_date_range(date_range)

            # 确定date范围
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # statistics各Platform活跃度
            platform_activity = defaultdict(lambda: {
                "total_updates": 0,
                "days_active": set(),
                "news_count": 0,
                "hourly_distribution": Counter()
            })

            # 遍历date范围
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        platform_activity[platform_name]["news_count"] += len(titles)
                        platform_activity[platform_name]["days_active"].add(current_date.strftime("%Y-%m-%d"))

                        # statisticsUpdate次数（基于file数量）
                        platform_activity[platform_name]["total_updates"] += len(timestamps)

                        # statisticstime分布（基于file名中的time）
                        for filename in timestamps.keys():
                            # Failed to parse file名中的hour（格式：HHMM.txt）
                            match = re.match(r'(\d{2})(\d{2})\.txt', filename)
                            if match:
                                hour = int(match.group(1))
                                platform_activity[platform_name]["hourly_distribution"][hour] += 1

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 转换为可序列化的格式
            result_activity = {}
            for platform, stats in platform_activity.items():
                days_count = len(stats["days_active"])
                avg_news_per_day = stats["news_count"] / days_count if days_count > 0 else 0

                # 找出最活跃的time段
                most_active_hours = stats["hourly_distribution"].most_common(3)

                result_activity[platform] = {
                    "total_updates": stats["total_updates"],
                    "news_count": stats["news_count"],
                    "days_active": days_count,
                    "avg_news_per_day": round(avg_news_per_day, 2),
                    "most_active_hours": [
                        {"hour": f"{hour:02d}:00", "count": count}
                        for hour, count in most_active_hours
                    ],
                    "activity_score": round(stats["news_count"] / max(days_count, 1), 2)
                }

            # 按活跃度sort
            sorted_platforms = sorted(
                result_activity.items(),
                key=lambda x: x[1]["activity_score"],
                reverse=True
            )

            return {
                "success": True,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_activity": dict(sorted_platforms),
                "most_active_platform": sorted_platforms[0][0] if sorted_platforms else None,
                "total_platforms": len(result_activity)
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

    def analyze_topic_lifecycle(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        话题生命周期analysis - 追踪话题从出现到消失的完整周期

        Args:
            topic: 话题关键词
            date_range: date范围（optional）
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **default**: When not specifieddefaultanalysis最近7天

        Returns:
            话题生命周期analysisresult

        Examples:
            用户询问示例：
            - "analysis'人工智能'这个话题的生命周期"
            - "看看'iPhone'话题是昙花一现还是持续hot topic"
            - "追踪'比特币'话题的热度变化"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.analyze_topic_lifecycle(
            ...     topic="人工智能",
            ...     date_range={"start": "2025-10-18", "end": "2025-10-25"}
            ... )
            >>> print(result['lifecycle_stage'])
        """
        try:
            # 参数Validate
            topic = validate_keyword(topic)

            # Processdate范围（When not specifieddefault最近7天）
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # default最近7天
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # 收集话题historydata
            lifecycle_data = []
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # statistics该日的话题出现次数
                    count = 0
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1

                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count
                    })

                except DataNotFoundError:
                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0
                    })

                current_date += timedelta(days=1)

            # 计算analysis天数
            total_days = (end_date - start_date).days + 1

            # analysis生命周期阶段
            counts = [item["count"] for item in lifecycle_data]

            if not any(counts):
                time_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"在 {time_desc} 内未找到话题 '{topic}'",
                    suggestion="请尝试其他话题或扩大time范围"
                )

            # 找到首次出现和最后出现
            first_appearance = next((item["date"] for item in lifecycle_data if item["count"] > 0), None)
            last_appearance = next((item["date"] for item in reversed(lifecycle_data) if item["count"] > 0), None)

            # 计算峰值
            max_count = max(counts)
            peak_index = counts.index(max_count)
            peak_date = lifecycle_data[peak_index]["date"]

            # 计算平均值和标准差（简单实现）
            non_zero_counts = [c for c in counts if c > 0]
            avg_count = sum(non_zero_counts) / len(non_zero_counts) if non_zero_counts else 0

            # 判断生命周期阶段
            recent_counts = counts[-3:]  # 最近3天
            early_counts = counts[:3]    # 前3天

            if sum(recent_counts) > sum(early_counts):
                lifecycle_stage = "上升期"
            elif sum(recent_counts) < sum(early_counts) * 0.5:
                lifecycle_stage = "衰退期"
            elif max_count in recent_counts:
                lifecycle_stage = "爆发期"
            else:
                lifecycle_stage = "稳定期"

            # 分类：昙花一现 vs 持续hot topic
            active_days = sum(1 for c in counts if c > 0)

            if active_days <= 2 and max_count > avg_count * 2:
                topic_type = "昙花一现"
            elif active_days >= total_days * 0.6:
                topic_type = "持续hot topic"
            else:
                topic_type = "周期性hot topic"

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "lifecycle_data": lifecycle_data,
                "analysis": {
                    "first_appearance": first_appearance,
                    "last_appearance": last_appearance,
                    "peak_date": peak_date,
                    "peak_count": max_count,
                    "active_days": active_days,
                    "avg_daily_mentions": round(avg_count, 2),
                    "lifecycle_stage": lifecycle_stage,
                    "topic_type": topic_type
                }
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

    def detect_viral_topics(
        self,
        threshold: float = 3.0,
        time_window: int = 24
    ) -> Dict:
        """
        abnormal热度检测 - 自动识别突然爆火的话题

        Args:
            threshold: 热度突增倍数阈值
            time_window: 检测time窗口（hour）

        Returns:
            爆火话题list

        Examples:
            用户询问示例：
            - "检测today有哪些突然爆火的话题"
            - "看看有没有热度abnormal的news"
            - "预警可能的重大事件"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.detect_viral_topics(
            ...     threshold=3.0,
            ...     time_window=24
            ... )
            >>> print(result['viral_topics'])
        """
        try:
            # 参数Validate
            if threshold < 1.0:
                raise InvalidParameterError(
                    "threshold 必须greater thanequal to 1.0",
                    suggestion="推荐值：2.0-5.0"
                )

            time_window = validate_limit(time_window, default=24, max_limit=72)

            # 读取current和之前的data
            current_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # 读取yesterday的data作为基准
            yesterday = datetime.now() - timedelta(days=1)
            try:
                previous_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                    date=yesterday
                )
            except DataNotFoundError:
                previous_all_titles = {}

            # statisticscurrent的关键词频率
            current_keywords = Counter()
            current_keyword_titles = defaultdict(list)

            for _, titles in current_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    current_keywords.update(keywords)

                    for kw in keywords:
                        current_keyword_titles[kw].append(title)

            # statistics之前的关键词频率
            previous_keywords = Counter()

            for _, titles in previous_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    previous_keywords.update(keywords)

            # 检测abnormal热度
            viral_topics = []

            for keyword, current_count in current_keywords.items():
                previous_count = previous_keywords.get(keyword, 0)

                # 计算增长倍数
                if previous_count == 0:
                    # 新出现的话题
                    if current_count >= 5:  # to少出现5次才认为是爆火
                        growth_rate = float('inf')
                        is_viral = True
                    else:
                        continue
                else:
                    growth_rate = current_count / previous_count
                    is_viral = growth_rate >= threshold

                if is_viral:
                    viral_topics.append({
                        "keyword": keyword,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth_rate": round(growth_rate, 2) if growth_rate != float('inf') else "新话题",
                        "sample_titles": current_keyword_titles[keyword][:3],
                        "alert_level": "高" if growth_rate > threshold * 2 else "中"
                    })

            # 按增长率sort
            viral_topics.sort(
                key=lambda x: x["current_count"] if x["growth_rate"] == "新话题" else x["growth_rate"],
                reverse=True
            )

            if not viral_topics:
                return {
                    "success": True,
                    "viral_topics": [],
                    "total_detected": 0,
                    "message": f"未检测到热度增长exceed {threshold} 倍的话题"
                }

            return {
                "success": True,
                "viral_topics": viral_topics,
                "total_detected": len(viral_topics),
                "threshold": threshold,
                "time_window": time_window,
                "detection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def predict_trending_topics(
        self,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        话题预测 - 基于historydata预测未来可能的hot topic

        Args:
            lookahead_hours: 预测未来多少hour
            confidence_threshold: 置信度阈值

        Returns:
            预测的潜力话题list

        Examples:
            用户询问示例：
            - "预测接下来6hour可能的hot topic话题"
            - "有哪些话题可能会火起来"
            - "早期发现潜力话题"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.predict_trending_topics(
            ...     lookahead_hours=6,
            ...     confidence_threshold=0.7
            ... )
            >>> print(result['predicted_topics'])
        """
        try:
            # 参数Validate
            lookahead_hours = validate_limit(lookahead_hours, default=6, max_limit=48)

            if not 0 <= confidence_threshold <= 1:
                raise InvalidParameterError(
                    "confidence_threshold 必须在 0 到 1 之间",
                    suggestion="推荐值：0.6-0.8"
                )

            # 收集最近3天的data用于预测
            keyword_trends = defaultdict(list)

            for days_ago in range(3, 0, -1):
                date = datetime.now() - timedelta(days=days_ago)

                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=date
                    )

                    # statistics关键词
                    keywords_count = Counter()
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            keywords = self._extract_keywords(title)
                            keywords_count.update(keywords)

                    # record每个关键词的historydata
                    for keyword, count in keywords_count.items():
                        keyword_trends[keyword].append(count)

                except DataNotFoundError:
                    pass

            # 添加today的data
            try:
                all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

                keywords_count = Counter()
                keyword_titles = defaultdict(list)

                for _, titles in all_titles.items():
                    for title in titles.keys():
                        keywords = self._extract_keywords(title)
                        keywords_count.update(keywords)

                        for kw in keywords:
                            keyword_titles[kw].append(title)

                for keyword, count in keywords_count.items():
                    keyword_trends[keyword].append(count)

            except DataNotFoundError:
                raise DataNotFoundError(
                    "未找到today的data",
                    suggestion="Please wait爬虫任务完成"
                )

            # 预测潜力话题
            predicted_topics = []

            for keyword, trend_data in keyword_trends.items():
                if len(trend_data) < 2:
                    continue

                # 简单的线性趋势预测
                # 计算增长率
                recent_value = trend_data[-1]
                previous_value = trend_data[-2] if len(trend_data) >= 2 else 0

                if previous_value == 0:
                    if recent_value >= 3:
                        growth_rate = 1.0
                    else:
                        continue
                else:
                    growth_rate = (recent_value - previous_value) / previous_value

                # 判断是否是上升趋势
                if growth_rate > 0.3:  # 增长exceed30%
                    # 计算置信度（基于趋势的稳定性）
                    if len(trend_data) >= 3:
                        # Check是否连续增长
                        is_consistent = all(
                            trend_data[i] <= trend_data[i+1]
                            for i in range(len(trend_data)-1)
                        )
                        confidence = 0.9 if is_consistent else 0.7
                    else:
                        confidence = 0.6

                    if confidence >= confidence_threshold:
                        predicted_topics.append({
                            "keyword": keyword,
                            "current_count": recent_value,
                            "growth_rate": round(growth_rate * 100, 2),
                            "confidence": round(confidence, 2),
                            "trend_data": trend_data,
                            "prediction": "上升趋势，可能成为hot topic",
                            "sample_titles": keyword_titles.get(keyword, [])[:3]
                        })

            # 按置信度和增长率sort
            predicted_topics.sort(
                key=lambda x: (x["confidence"], x["growth_rate"]),
                reverse=True
            )

            return {
                "success": True,
                "predicted_topics": predicted_topics[:20],  # returnTOP 20
                "total_predicted": len(predicted_topics),
                "lookahead_hours": lookahead_hours,
                "confidence_threshold": confidence_threshold,
                "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "预测基于history趋势，实际result可能有偏差"
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

    # ==================== 辅助方法 ====================

    def _extract_keywords(self, title: str, min_length: int = 2) -> List[str]:
        """
        从title中提取关键词（简单实现）

        Args:
            title: title文本
            min_length: 最小关键词长度

        Returns:
            关键词list
        """
        # 移除URL和特殊字符
        title = re.sub(r'http[s]?://\S+', '', title)
        title = re.sub(r'[^\w\s]', ' ', title)

        # 简单分词（按空格和常见分隔符）
        words = re.split(r'[\s，。！？、]+', title)

        # 过滤停用词和短词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

        keywords = [
            word.strip() for word in words
            if word.strip() and len(word.strip()) >= min_length and word.strip() not in stopwords
        ]

        return keywords

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数（0-1之间）
        """
        # use SequenceMatcher 计算相似度
        return SequenceMatcher(None, text1, text2).ratio()

    def _find_unique_topics(self, platform_stats: Dict) -> Dict[str, List[str]]:
        """
        找出各Platform独有的hot topic话题

        Args:
            platform_stats: Platformstatisticsdata

        Returns:
            各Platform独有话题dictionary
        """
        unique_topics = {}

        # Get每个Platform的TOP关键词
        platform_keywords = {}
        for platform, stats in platform_stats.items():
            top_keywords = set([kw for kw, _ in stats["top_keywords"].most_common(10)])
            platform_keywords[platform] = top_keywords

        # 找出独有关键词
        for platform, keywords in platform_keywords.items():
            # 找出其他Platform的所有关键词
            other_keywords = set()
            for other_platform, other_kws in platform_keywords.items():
                if other_platform != platform:
                    other_keywords.update(other_kws)

            # 找出独有的
            unique = keywords - other_keywords
            if unique:
                unique_topics[platform] = list(unique)[:5]  # 最多5个

        return unique_topics
