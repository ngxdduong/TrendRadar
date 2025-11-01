"""
智能news检索工具

提供模糊search、linkquery、history相关news检索等高级search功能。
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from ..services.data_service import DataService
from ..utils.validators import validate_keyword, validate_limit
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


class SearchTools:
    """智能news检索工具类"""

    def __init__(self, project_root: str = None):
        """
        Initialize智能检索工具

        Args:
            project_root: 项目根directory
        """
        self.data_service = DataService(project_root)
        # 中文停用词list
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这', '那', '来', '被', '与', '为', '对', '将', '从',
            '以', '及', '等', '但', '或', '而', '于', '中', '由', '可', 'can', '已',
            '已经', '还', '更', '最', '再', '因为', '所以', '如果', '虽然', '然而'
        }

    def search_news_unified(
        self,
        query: str,
        search_mode: str = "keyword",
        date_range: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        sort_by: str = "relevance",
        threshold: float = 0.6,
        include_url: bool = False
    ) -> Dict:
        """
        统一newssearch工具 - 整合多种search模式

        Args:
            query: querycontent（必需）- 关键词、content片段或实体名称
            search_mode: search模式，optional值：
                - "keyword": 精确关键词匹配（default）
                - "fuzzy": 模糊content匹配（use相似度算法）
                - "entity": 实体名称search（自动按权重sort）
            date_range: date范围（optional）
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                       - **default**: When not specifieddefaultquerytoday
                       - **Note**: start和endcan相同（表示单日query）
            platforms: Platform过滤list，如 ['zhihu', 'weibo']
            limit: return条数limit，default50
            sort_by: sort方式，optional值：
                - "relevance": 按相关度sort（default）
                - "weight": 按news权重sort
                - "date": 按datesort
            threshold: 相似度阈值（仅fuzzy模式有效），0-1之间，default0.6
            include_url: 是否includeURLlink，defaultFalse（节省token）

        Returns:
            searchresultdictionary，include匹配的newslist

        Examples:
            - search_news_unified(query="人工智能", search_mode="keyword")
            - search_news_unified(query="特斯拉降价", search_mode="fuzzy", threshold=0.4)
            - search_news_unified(query="马斯克", search_mode="entity", limit=20)
            - search_news_unified(query="iPhone 16", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        """
        try:
            # 参数Validate
            query = validate_keyword(query)

            if search_mode not in ["keyword", "fuzzy", "entity"]:
                raise InvalidParameterError(
                    f"无效的search模式: {search_mode}",
                    suggestion="Supported modes: keyword, fuzzy, entity"
                )

            if sort_by not in ["relevance", "weight", "date"]:
                raise InvalidParameterError(
                    f"无效的sort方式: {sort_by}",
                    suggestion="support的sort: relevance, weight, date"
                )

            limit = validate_limit(limit, default=50)
            threshold = max(0.0, min(1.0, threshold))

            # Processdate范围
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 不指定date时，uselatest可用datadate（而非 datetime.now()）
                earliest, latest = self.data_service.get_available_date_range()

                if latest is None:
                    # 没有任何可用data
                    return {
                        "success": False,
                        "error": {
                            "code": "NO_DATA_AVAILABLE",
                            "message": "output directory下没有可用的newsdata",
                            "suggestion": "请先运行爬虫Generatedata，或Check output directory"
                        }
                    }

                # uselatest可用date
                start_date = end_date = latest

            # 收集所有匹配的news
            all_matches = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # 根据search模式Execute不同的search逻辑
                    if search_mode == "keyword":
                        matches = self._search_by_keyword_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )
                    elif search_mode == "fuzzy":
                        matches = self._search_by_fuzzy_mode(
                            query, all_titles, id_to_name, current_date, threshold, include_url
                        )
                    else:  # entity
                        matches = self._search_by_entity_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )

                    all_matches.extend(matches)

                except DataNotFoundError:
                    # 该date没有data，继续下一天
                    pass

                current_date += timedelta(days=1)

            if not all_matches:
                # Get可用date范围用于errorhint
                earliest, latest = self.data_service.get_available_date_range()

                # 判断time范围描述
                if start_date.date() == datetime.now().date() and start_date == end_date:
                    time_desc = "today"
                elif start_date == end_date:
                    time_desc = start_date.strftime("%Y-%m-%d")
                else:
                    time_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

                # 构建errormessage
                if earliest and latest:
                    available_desc = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
                    message = f"未找到匹配的news（query范围: {time_desc}，可用data: {available_desc}）"
                else:
                    message = f"未找到匹配的news（{time_desc}）"

                result = {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": query,
                    "search_mode": search_mode,
                    "time_range": time_desc,
                    "message": message
                }
                return result

            # 统一sort逻辑
            if sort_by == "relevance":
                all_matches.sort(key=lambda x: x.get("similarity_score", 1.0), reverse=True)
            elif sort_by == "weight":
                from .analytics import calculate_news_weight
                all_matches.sort(key=lambda x: calculate_news_weight(x), reverse=True)
            elif sort_by == "date":
                all_matches.sort(key=lambda x: x.get("date", ""), reverse=True)

            # limitreturn数量
            results = all_matches[:limit]

            # 构建time范围描述（正确判断是否为today）
            if start_date.date() == datetime.now().date() and start_date == end_date:
                time_range_desc = "today"
            elif start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_matches),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "search_mode": search_mode,
                    "query": query,
                    "platforms": platforms or "所有Platform",
                    "time_range": time_range_desc,
                    "sort_by": sort_by
                },
                "results": results
            }

            if search_mode == "fuzzy":
                result["summary"]["threshold"] = threshold
                if len(all_matches) < limit:
                    result["note"] = f"模糊search模式下，相似度阈值 {threshold} 仅匹配到 {len(all_matches)} 条result"

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

    def _search_by_keyword_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """
        关键词search模式（精确匹配）

        Args:
            query: Search keyword
            all_titles: 所有titledictionary
            id_to_name: PlatformID到名称映射
            current_date: Current date

        Returns:
            匹配的newslist
        """
        matches = []
        query_lower = query.lower()

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 精确include判断
                if query_lower in title.lower():
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,  # 精确匹配，相似度为1
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # 条件性添加 URL 字段
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_fuzzy_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        threshold: float,
        include_url: bool
    ) -> List[Dict]:
        """
        模糊search模式（use相似度算法）

        Args:
            query: searchcontent
            all_titles: 所有titledictionary
            id_to_name: PlatformID到名称映射
            current_date: Current date
            threshold: 相似度阈值

        Returns:
            匹配的newslist
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 模糊匹配
                is_match, similarity = self._fuzzy_match(query, title, threshold)

                if is_match:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": round(similarity, 4),
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # 条件性添加 URL 字段
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_entity_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """
        实体search模式（自动按权重sort）

        Args:
            query: 实体名称
            all_titles: 所有titledictionary
            id_to_name: PlatformID到名称映射
            current_date: Current date

        Returns:
            匹配的newslist
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 实体search：精确include实体名称
                if query in title:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # 条件性添加 URL 字段
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0-1之间)
        """
        # use difflib.SequenceMatcher 计算序列相似度
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _fuzzy_match(self, query: str, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        模糊匹配函数

        Args:
            query: query文本
            text: 待匹配文本
            threshold: 匹配阈值

        Returns:
            (是否匹配, 相似度分数)
        """
        # 直接include判断
        if query.lower() in text.lower():
            return True, 1.0

        # 计算整体相似度
        similarity = self._calculate_similarity(query, text)
        if similarity >= threshold:
            return True, similarity

        # 分词后的部分匹配
        query_words = set(self._extract_keywords(query))
        text_words = set(self._extract_keywords(text))

        if not query_words or not text_words:
            return False, 0.0

        # 计算关键词重合度
        common_words = query_words & text_words
        keyword_overlap = len(common_words) / len(query_words)

        if keyword_overlap >= 0.5:  # 50%的关键词重合
            return True, keyword_overlap

        return False, similarity

    def _extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: input文本
            min_length: 最小词长

        Returns:
            关键词list
        """
        # 移除URL和特殊字符
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # 移除方括号content

        # use正则表达式分词（中文和英文）
        words = re.findall(r'[\w]+', text)

        # 过滤停用词和短词
        keywords = [
            word for word in words
            if word and len(word) >= min_length and word not in self.stopwords
        ]

        return keywords

    def _calculate_keyword_overlap(self, keywords1: List[str], keywords2: List[str]) -> float:
        """
        计算两个关键词list的重合度

        Args:
            keywords1: 关键词list1
            keywords2: 关键词list2

        Returns:
            重合度分数 (0-1之间)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        # Jaccard 相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def search_related_news_history(
        self,
        reference_text: str,
        time_preset: str = "yesterday",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold: float = 0.4,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        在historydata中search与给定news相关的news

        Args:
            reference_text: 参考newstitle或content
            time_preset: time范围预设值，optional：
                - "yesterday": yesterday
                - "last_week": 上周 (7天)
                - "last_month": 上个月 (30天)
                - "custom": customdate范围（need提供 start_date 和 end_date）
            start_date: custom开始date（仅当 time_preset="custom" 时有效）
            end_date: custom结束date（仅当 time_preset="custom" 时有效）
            threshold: 相似度阈值 (0-1之间)，default0.4
            limit: return条数limit，default50
            include_url: 是否includeURLlink，defaultFalse（节省token）

        Returns:
            searchresultdictionary，include相关newslist

        Example:
            >>> tools = SearchTools()
            >>> result = tools.search_related_news_history(
            ...     reference_text="人工智能技术突破",
            ...     time_preset="last_week",
            ...     threshold=0.4,
            ...     limit=50
            ... )
            >>> for news in result['results']:
            ...     print(f"{news['date']}: {news['title']} (相似度: {news['similarity_score']})")
        """
        try:
            # 参数Validate
            reference_text = validate_keyword(reference_text)
            threshold = max(0.0, min(1.0, threshold))
            limit = validate_limit(limit, default=50)

            # 确定querydate范围
            today = datetime.now()

            if time_preset == "yesterday":
                search_start = today - timedelta(days=1)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_week":
                search_start = today - timedelta(days=7)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_month":
                search_start = today - timedelta(days=30)
                search_end = today - timedelta(days=1)
            elif time_preset == "custom":
                if not start_date or not end_date:
                    raise InvalidParameterError(
                        "customtime范围need提供 start_date 和 end_date",
                        suggestion="Please provide start_date 和 end_date 参数"
                    )
                search_start = start_date
                search_end = end_date
            else:
                raise InvalidParameterError(
                    f"不support的time范围: {time_preset}",
                    suggestion="请use 'yesterday', 'last_week', 'last_month' 或 'custom'"
                )

            # 提取参考文本的关键词
            reference_keywords = self._extract_keywords(reference_text)

            if not reference_keywords:
                raise InvalidParameterError(
                    "无法从参考文本中提取关键词",
                    suggestion="Please provide更详细的文本content"
                )

            # 收集所有相关news
            all_related_news = []
            current_date = search_start

            while current_date <= search_end:
                try:
                    # 读取该date的data
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(current_date)

                    # search相关news
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title, info in titles.items():
                            # 计算title相似度
                            title_similarity = self._calculate_similarity(reference_text, title)

                            # 提取title关键词
                            title_keywords = self._extract_keywords(title)

                            # 计算关键词重合度
                            keyword_overlap = self._calculate_keyword_overlap(
                                reference_keywords,
                                title_keywords
                            )

                            # 综合相似度 (70% 关键词重合 + 30% 文本相似度)
                            combined_score = keyword_overlap * 0.7 + title_similarity * 0.3

                            if combined_score >= threshold:
                                news_item = {
                                    "title": title,
                                    "platform": platform_id,
                                    "platform_name": platform_name,
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "similarity_score": round(combined_score, 4),
                                    "keyword_overlap": round(keyword_overlap, 4),
                                    "text_similarity": round(title_similarity, 4),
                                    "common_keywords": list(set(reference_keywords) & set(title_keywords)),
                                    "rank": info["ranks"][0] if info["ranks"] else 0
                                }

                                # 条件性添加 URL 字段
                                if include_url:
                                    news_item["url"] = info.get("url", "")
                                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                                all_related_news.append(news_item)

                except DataNotFoundError:
                    # 该date没有data，继续下一天
                    pass
                except Exception as e:
                    # recorderror但继续Process其他date
                    print(f"Warning: Processdate {current_date.strftime('%Y-%m-%d')} 时出错: {e}")

                # 移动到下一天
                current_date += timedelta(days=1)

            if not all_related_news:
                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": reference_text,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    },
                    "message": "未找到相关news"
                }

            # 按相似度sort
            all_related_news.sort(key=lambda x: x["similarity_score"], reverse=True)

            # limitreturn数量
            results = all_related_news[:limit]

            # statisticsinformation
            platform_distribution = Counter([news["platform"] for news in all_related_news])
            date_distribution = Counter([news["date"] for news in all_related_news])

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_related_news),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_text": reference_text,
                    "reference_keywords": reference_keywords,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    }
                },
                "results": results,
                "statistics": {
                    "platform_distribution": dict(platform_distribution),
                    "date_distribution": dict(date_distribution),
                    "avg_similarity": round(
                        sum([news["similarity_score"] for news in all_related_news]) / len(all_related_news),
                        4
                    ) if all_related_news else 0.0
                }
            }

            if len(all_related_news) < limit:
                result["note"] = f"相关性阈值 {threshold} 下仅找到 {len(all_related_news)} 条相关news"

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
