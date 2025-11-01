"""
dataquery工具

实现P0核心的dataquery工具。
"""

from typing import Dict, List, Optional

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_date_range,
    validate_top_n,
    validate_mode,
    validate_date_query
)
from ..utils.errors import MCPError


class DataQueryTools:
    """dataquery工具类"""

    def __init__(self, project_root: str = None):
        """
        Initializedataquery工具

        Args:
            project_root: 项目根directory
        """
        self.data_service = DataService(project_root)

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Getlatest一批爬取的newsdata

        Args:
            platforms: List of platform IDs，如 ['zhihu', 'weibo']
            limit: return条数limit，default20
            include_url: 是否includeURLlink，defaultFalse（节省token）

        Returns:
            newslistdictionary

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_latest_news(platforms=['zhihu'], limit=10)
            >>> print(result['total'])
            10
        """
        try:
            # 参数Validate
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Getdata
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
        date_range: Optional[Dict] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        按关键词searchhistorynews

        Args:
            keyword: Search keyword（必需）
            date_range: date范围，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            platforms: Platform过滤list
            limit: return条数limit（optional，defaultreturn所有）

        Returns:
            searchresultdictionary

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.search_news_by_keyword(
            ...     keyword="人工智能",
            ...     date_range={"start": "2025-10-01", "end": "2025-10-11"},
            ...     limit=50
            ... )
            >>> print(result['total'])
        """
        try:
            # 参数Validate
            keyword = validate_keyword(keyword)
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)

            if limit is not None:
                limit = validate_limit(limit, default=100)

            # searchdata
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
        mode: Optional[str] = None
    ) -> Dict:
        """
        Get个人关注词的news出现频率statistics

        Note：本工具基于 config/frequency_words.txt 中的个人关注词list进行statistics，
        而不是自动从news中提取hot topic话题。这是一个个人可定制的关注词list，
        用户can根据自己的兴趣添加或Delete关注词。

        Args:
            top_n: returnTOP N关注词，default10
            mode: 模式 - daily(当日累计), current(latest一批), incremental(增量)

        Returns:
            关注词频率statisticsdictionary，include每个关注词在news中出现的次数

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_trending_topics(top_n=5, mode="current")
            >>> print(len(result['topics']))
            5
            >>> # return的是你在 frequency_words.txt 中设置的关注词的频率statistics
        """
        try:
            # 参数Validate
            top_n = validate_top_n(top_n, default=10)
            valid_modes = ["daily", "current", "incremental"]
            mode = validate_mode(mode, valid_modes, default="current")

            # Get趋势话题
            trending_result = self.data_service.get_trending_topics(
                top_n=top_n,
                mode=mode
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
        date_query: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        按datequerynews，support自然语言date

        Args:
            date_query: Date query string（optional，default"today"），support：
                - 相对date：today、yesterday、the day before yesterday、3天前、yesterday、3 days ago
                - 星期：上周一、本周三、last monday、this friday
                - 绝对date：2025-10-10、10月10日、2025年10月10日
            platforms: List of platform IDs，如 ['zhihu', 'weibo']
            limit: return条数limit，default50
            include_url: 是否includeURLlink，defaultFalse（节省token）

        Returns:
            newslistdictionary

        Example:
            >>> tools = DataQueryTools()
            >>> # 不指定date，defaultquerytoday
            >>> result = tools.get_news_by_date(platforms=['zhihu'], limit=20)
            >>> # 指定date
            >>> result = tools.get_news_by_date(
            ...     date_query="yesterday",
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
            >>> print(result['total'])
            20
        """
        try:
            # 参数Validate - defaulttoday
            if date_query is None:
                date_query = "today"
            target_date = validate_date_query(date_query)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Getdata
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
                "date_query": date_query,
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

