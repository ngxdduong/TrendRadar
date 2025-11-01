"""
data访问服务

提供统一的dataquery接口,封装data访问逻辑。
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .cache_service import get_cache
from .parser_service import ParserService
from ..utils.errors import DataNotFoundError


class DataService:
    """data访问服务类"""

    def __init__(self, project_root: str = None):
        """
        Initializedata服务

        Args:
            project_root: 项目根directory
        """
        self.parser = ParserService(project_root)
        self.cache = get_cache()

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Getlatest一批爬取的newsdata

        Args:
            platforms: List of platform IDs,None表示所有Platform
            limit: return条数limit
            include_url: 是否includeURLlink,defaultFalse(节省token)

        Returns:
            newslist

        Raises:
            DataNotFoundError: datadoes not exist
        """
        # 尝试从缓存Get
        cache_key = f"latest_news:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=900)  # 15minute缓存
        if cached:
            return cached

        # 读取today的data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=None,
            platform_ids=platforms
        )

        # Getlatest的filetime
        if timestamps:
            latest_timestamp = max(timestamps.values())
            fetch_time = datetime.fromtimestamp(latest_timestamp)
        else:
            fetch_time = datetime.now()

        # 转换为newslist
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 取第一个rank
                rank = info["ranks"][0] if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": rank,
                    "timestamp": fetch_time.strftime("%Y-%m-%d %H:%M:%S")
                }

                # 条件性添加 URL 字段
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # 按ranksort
        news_list.sort(key=lambda x: x["rank"])

        # limitreturn数量
        result = news_list[:limit]

        # 缓存result
        self.cache.set(cache_key, result)

        return result

    def get_news_by_date(
        self,
        target_date: datetime,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        按指定dateGetnews

        Args:
            target_date: 目标date
            platforms: List of platform IDs,None表示所有Platform
            limit: return条数limit
            include_url: 是否includeURLlink,defaultFalse(节省token)

        Returns:
            newslist

        Raises:
            DataNotFoundError: datadoes not exist

        Examples:
            >>> service = DataService()
            >>> news = service.get_news_by_date(
            ...     target_date=datetime(2025, 10, 10),
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
        """
        # 尝试从缓存Get
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"news_by_date:{date_str}:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=1800)  # 30minute缓存
        if cached:
            return cached

        # 读取指定date的data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=target_date,
            platform_ids=platforms
        )

        # 转换为newslist
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 计算平均rank
                avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": info["ranks"][0] if info["ranks"] else 0,
                    "avg_rank": round(avg_rank, 2),
                    "count": len(info["ranks"]),
                    "date": date_str
                }

                # 条件性添加 URL 字段
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # 按ranksort
        news_list.sort(key=lambda x: x["rank"])

        # limitreturn数量
        result = news_list[:limit]

        # 缓存result(historydata缓存更久)
        self.cache.set(cache_key, result)

        return result

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        按关键词searchnews

        Args:
            keyword: Search keyword
            date_range: date范围 (start_date, end_date)
            platforms: Platform过滤list
            limit: return条数limit(optional)

        Returns:
            searchresultdictionary

        Raises:
            DataNotFoundError: datadoes not exist
        """
        # 确定searchdate范围
        if date_range:
            start_date, end_date = date_range
        else:
            # defaultsearchtoday
            start_date = end_date = datetime.now()

        # 收集所有匹配的news
        results = []
        platform_distribution = Counter()

        # 遍历date范围
        current_date = start_date
        while current_date <= end_date:
            try:
                all_titles, id_to_name, _ = self.parser.read_all_titles_for_date(
                    date=current_date,
                    platform_ids=platforms
                )

                # searchinclude关键词的title
                for platform_id, titles in all_titles.items():
                    platform_name = id_to_name.get(platform_id, platform_id)

                    for title, info in titles.items():
                        if keyword.lower() in title.lower():
                            # 计算平均rank
                            avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                            results.append({
                                "title": title,
                                "platform": platform_id,
                                "platform_name": platform_name,
                                "ranks": info["ranks"],
                                "count": len(info["ranks"]),
                                "avg_rank": round(avg_rank, 2),
                                "url": info.get("url", ""),
                                "mobileUrl": info.get("mobileUrl", ""),
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            platform_distribution[platform_id] += 1

            except DataNotFoundError:
                # 该date没有data,继续下一天
                pass

            # 下一天
            current_date += timedelta(days=1)

        if not results:
            raise DataNotFoundError(
                f"未找到include关键词 '{keyword}' 的news",
                suggestion="请尝试其他关键词或扩大date范围"
            )

        # 计算statisticsinformation
        total_ranks = []
        for item in results:
            total_ranks.extend(item["ranks"])

        avg_rank = sum(total_ranks) / len(total_ranks) if total_ranks else 0

        # limitreturn数量(如果指定)
        total_found = len(results)
        if limit is not None and limit > 0:
            results = results[:limit]

        return {
            "results": results,
            "total": len(results),
            "total_found": total_found,
            "statistics": {
                "platform_distribution": dict(platform_distribution),
                "avg_rank": round(avg_rank, 2),
                "keyword": keyword
            }
        }

    def get_trending_topics(
        self,
        top_n: int = 10,
        mode: str = "current"
    ) -> Dict:
        """
        Get个人关注词的news出现频率statistics

        Note:本工具基于 config/frequency_words.txt 中的个人关注词list进行statistics,
        而不是自动从news中提取hot topic话题。用户cancustom这个关注词list。

        Args:
            top_n: returnTOP N关注词
            mode: 模式 - daily(当日累计), current(latest一批)

        Returns:
            关注词频率statisticsdictionary

        Raises:
            DataNotFoundError: datadoes not exist
        """
        # 尝试从缓存Get
        cache_key = f"trending_topics:{top_n}:{mode}"
        cached = self.cache.get(cache_key, ttl=1800)  # 30minute缓存
        if cached:
            return cached

        # 读取today的data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date()

        if not all_titles:
            raise DataNotFoundError(
                "未找到today的newsdata",
                suggestion="请确保爬虫已经运行并Generate了data"
            )

        # Load关键词配置
        word_groups = self.parser.parse_frequency_words()

        # 根据mode选择要Process的titledata
        titles_to_process = {}

        if mode == "daily":
            # daily模式:Process当天所有累计data
            titles_to_process = all_titles

        elif mode == "current":
            # current模式:只Processlatest一批data(latesttime戳的file)
            if timestamps:
                # 找出latest的time戳
                latest_timestamp = max(timestamps.values())

                # 重新读取,只Getlatesttime的data
                # 这里我们通过timestampsdictionary反查找latestfile对应的Platform
                latest_titles, _, _ = self.parser.read_all_titles_for_date()

                # 由于read_all_titles_for_datereturn所有file的合并data,
                # 我们need通过timestamps来过滤出latest批次
                # 简化实现:usecurrent所有data作为latest批次
                # (更精确的实现needParse服务support按time过滤)
                titles_to_process = latest_titles
            else:
                titles_to_process = all_titles

        else:
            raise ValueError(
                f"不Supported modes: {mode}。Supported modes: daily, current"
            )

        # statistics词频
        word_frequency = Counter()
        keyword_to_news = {}

        # 遍历要Process的title
        for platform_id, titles in titles_to_process.items():
            for title in titles.keys():
                # 对每个关键词组进行匹配
                for group in word_groups:
                    all_words = group.get("required", []) + group.get("normal", [])

                    for word in all_words:
                        if word and word in title:
                            word_frequency[word] += 1

                            if word not in keyword_to_news:
                                keyword_to_news[word] = []
                            keyword_to_news[word].append(title)

        # GetTOP N关键词
        top_keywords = word_frequency.most_common(top_n)

        # 构建话题list
        topics = []
        for keyword, frequency in top_keywords:
            matched_news = keyword_to_news.get(keyword, [])

            topics.append({
                "keyword": keyword,
                "frequency": frequency,
                "matched_news": len(set(matched_news)),  # 去重后的news数量
                "trend": "stable",  # TODO: needhistorydata来计算趋势
                "weight_score": 0.0  # TODO: need实现权重计算
            })

        # 构建result
        result = {
            "topics": topics,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "total_keywords": len(word_frequency),
            "description": self._get_mode_description(mode)
        }

        # 缓存result
        self.cache.set(cache_key, result)

        return result

    def _get_mode_description(self, mode: str) -> str:
        """Get模式描述"""
        descriptions = {
            "daily": "当日累计statistics",
            "current": "latest一批statistics"
        }
        return descriptions.get(mode, "未知模式")

    def get_current_config(self, section: str = "all") -> Dict:
        """
        Getcurrent系统配置

        Args:
            section: 配置节 - all/crawler/push/keywords/weights

        Returns:
            配置dictionary

        Raises:
            FileParseError: 配置File parse error
        """
        # 尝试从缓存Get
        cache_key = f"config:{section}"
        cached = self.cache.get(cache_key, ttl=3600)  # 1hour缓存
        if cached:
            return cached

        # Parseconfiguration file
        config_data = self.parser.parse_yaml_config()
        word_groups = self.parser.parse_frequency_words()

        # 根据sectionreturn对应配置
        if section == "all" or section == "crawler":
            crawler_config = {
                "enable_crawler": config_data.get("crawler", {}).get("enable_crawler", True),
                "use_proxy": config_data.get("crawler", {}).get("use_proxy", False),
                "request_interval": config_data.get("crawler", {}).get("request_interval", 1),
                "retry_times": 3,
                "platforms": [p["id"] for p in config_data.get("platforms", [])]
            }

        if section == "all" or section == "push":
            push_config = {
                "enable_notification": config_data.get("notification", {}).get("enable_notification", True),
                "enabled_channels": [],
                "message_batch_size": config_data.get("notification", {}).get("message_batch_size", 20),
                "push_window": config_data.get("notification", {}).get("push_window", {})
            }

            # 检测已配置的notification渠道
            webhooks = config_data.get("notification", {}).get("webhooks", {})
            if webhooks.get("feishu_url"):
                push_config["enabled_channels"].append("feishu")
            if webhooks.get("dingtalk_url"):
                push_config["enabled_channels"].append("dingtalk")
            if webhooks.get("wework_url"):
                push_config["enabled_channels"].append("wework")

        if section == "all" or section == "keywords":
            keywords_config = {
                "word_groups": word_groups,
                "total_groups": len(word_groups)
            }

        if section == "all" or section == "weights":
            weights_config = {
                "rank_weight": config_data.get("weight", {}).get("rank_weight", 0.6),
                "frequency_weight": config_data.get("weight", {}).get("frequency_weight", 0.3),
                "hotness_weight": config_data.get("weight", {}).get("hotness_weight", 0.1)
            }

        # 组装result
        if section == "all":
            result = {
                "crawler": crawler_config,
                "push": push_config,
                "keywords": keywords_config,
                "weights": weights_config
            }
        elif section == "crawler":
            result = crawler_config
        elif section == "push":
            result = push_config
        elif section == "keywords":
            result = keywords_config
        elif section == "weights":
            result = weights_config
        else:
            result = {}

        # 缓存result
        self.cache.set(cache_key, result)

        return result

    def get_available_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        扫描 output directory，return实际可用的date范围

        Returns:
            (最早date, latestdate) 元组，如果没有data则return (None, None)

        Examples:
            >>> service = DataService()
            >>> earliest, latest = service.get_available_date_range()
            >>> print(f"可用date范围：{earliest} to {latest}")
        """
        output_dir = self.parser.project_root / "output"

        if not output_dir.exists():
            return (None, None)

        available_dates = []

        # 遍历datefile夹
        for date_folder in output_dir.iterdir():
            if date_folder.is_dir() and not date_folder.name.startswith('.'):
                # Parsedate（格式: YYYY年MM月DD日）
                try:
                    date_match = re.match(r'(\d{4})年(\d{2})月(\d{2})日', date_folder.name)
                    if date_match:
                        folder_date = datetime(
                            int(date_match.group(1)),
                            int(date_match.group(2)),
                            int(date_match.group(3))
                        )
                        available_dates.append(folder_date)
                except Exception:
                    pass

        if not available_dates:
            return (None, None)

        return (min(available_dates), max(available_dates))

    def get_system_status(self) -> Dict:
        """
        Get系统运行状态

        Returns:
            系统状态dictionary
        """
        # Getdatastatistics
        output_dir = self.parser.project_root / "output"

        total_storage = 0
        oldest_record = None
        latest_record = None
        total_news = 0

        if output_dir.exists():
            # 遍历datefile夹
            for date_folder in output_dir.iterdir():
                if date_folder.is_dir():
                    # Parsedate
                    try:
                        date_str = date_folder.name
                        # 格式: YYYY年MM月DD日
                        date_match = re.match(r'(\d{4})年(\d{2})月(\d{2})日', date_str)
                        if date_match:
                            folder_date = datetime(
                                int(date_match.group(1)),
                                int(date_match.group(2)),
                                int(date_match.group(3))
                            )

                            if oldest_record is None or folder_date < oldest_record:
                                oldest_record = folder_date
                            if latest_record is None or folder_date > latest_record:
                                latest_record = folder_date

                    except:
                        pass

                    # 计算存储大小
                    for item in date_folder.rglob("*"):
                        if item.is_file():
                            total_storage += item.stat().st_size

        # 读取版本information
        version_file = self.parser.project_root / "version"
        version = "unknown"
        if version_file.exists():
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
            except:
                pass

        return {
            "system": {
                "version": version,
                "project_root": str(self.parser.project_root)
            },
            "data": {
                "total_storage": f"{total_storage / 1024 / 1024:.2f} MB",
                "oldest_record": oldest_record.strftime("%Y-%m-%d") if oldest_record else None,
                "latest_record": latest_record.strftime("%Y-%m-%d") if latest_record else None,
            },
            "cache": self.cache.get_stats(),
            "health": "healthy"
        }
