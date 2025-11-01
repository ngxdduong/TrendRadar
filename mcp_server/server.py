"""
TrendRadar MCP Server - FastMCP 2.0 Implementation

Provides production-grade MCP tool server using FastMCP 2.0.
Supports both stdio and HTTP transport modes.
"""

import json
from typing import List, Optional, Dict

from fastmcp import FastMCP

from .tools.data_query import DataQueryTools
from .tools.analytics import AnalyticsTools
from .tools.search_tools import SearchTools
from .tools.config_mgmt import ConfigManagementTools
from .tools.system import SystemManagementTools


# Create FastMCP 2.0 application
mcp = FastMCP('trendradar-news')

# Global tool instances (initialized on first request)
_tools_instances = {}


def _get_tools(project_root: Optional[str] = None):
    """Get or create tool instances (singleton pattern)"""
    if not _tools_instances:
        _tools_instances['data'] = DataQueryTools(project_root)
        _tools_instances['analytics'] = AnalyticsTools(project_root)
        _tools_instances['search'] = SearchTools(project_root)
        _tools_instances['config'] = ConfigManagementTools(project_root)
        _tools_instances['system'] = SystemManagementTools(project_root)
    return _tools_instances


# ==================== Data Query Tools ====================

@mcp.tool
async def get_latest_news(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Get the latest batch of crawled news data to quickly understand current hot topics

    Args:
        platforms: List of platform IDs, such as ['zhihu', 'weibo', 'douyin']
                   - When not specified：use config.yaml 中配置的所有Platform
                   - Supported platforms来自 config/config.yaml 的 platforms 配置
                   - 每个Platform都有对应的name字段（如"Zhihu"、"Weibo"），方便AI识别
        limit: return条数limit，default50，最大1000
               Note：实际return数量可能少于请求值，取决于current可用的news总数
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的newslist

    **Important：data展示建议**
    本工具会return完整的newslist（通常50条）给你。但请Note：
    - **工具return**：完整的50条data ✅
    - **建议展示**：向用户展示全部data，除非用户明确要求总结
    - **用户期望**：用户可能need完整data，请谨慎总结

    **何时can总结**：
    - 用户明确说"给我总结一下"或"挑重点说"
    - data量exceed100条时，可先展示部分并询问是否查看全部

    **Note**：如果用户询问"为什么只显示了部分"，说明他们need完整data
    """
    tools = _get_tools()
    result = tools['data'].get_latest_news(platforms=platforms, limit=limit, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_trending_topics(
    top_n: int = 10,
    mode: str = 'current'
) -> str:
    """
    Get个人关注词的news出现频率statistics（基于 config/frequency_words.txt）

    Note：本工具不是自动提取newshot topic，而是statistics你在 config/frequency_words.txt 中
    设置的个人关注词在news中出现的频率。你cancustom这个关注词list。

    Args:
        top_n: returnTOP N关注词，default10
        mode: 模式选择
            - daily: 当日累计datastatistics
            - current: latest一批datastatistics（default）

    Returns:
        JSON格式的关注词频率statisticslist
    """
    tools = _get_tools()
    result = tools['data'].get_trending_topics(top_n=top_n, mode=mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_news_by_date(
    date_query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Get指定date的newsdata，用于historydataanalysis和对比

    Args:
        date_query: datequery，optional格式:
            - 自然语言: "today", "yesterday", "the day before yesterday", "3天前"
            - 标准date: "2024-01-15", "2024/01/15"
            - Default value: "today"（节省token）
        platforms: List of platform IDs，如 ['zhihu', 'weibo', 'douyin']
                   - When not specified：use config.yaml 中配置的所有Platform
                   - Supported platforms来自 config/config.yaml 的 platforms 配置
                   - 每个Platform都有对应的name字段（如"Zhihu"、"Weibo"），方便AI识别
        limit: return条数limit，default50，最大1000
               Note：实际return数量可能少于请求值，取决于指定date的news总数
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的newslist，includetitle、Platform、rank等information

    **Important：data展示建议**
    本工具会return完整的newslist（通常50条）给你。但请Note：
    - **工具return**：完整的50条data ✅
    - **建议展示**：向用户展示全部data，除非用户明确要求总结
    - **用户期望**：用户可能need完整data，请谨慎总结

    **何时can总结**：
    - 用户明确说"给我总结一下"或"挑重点说"
    - data量exceed100条时，可先展示部分并询问是否查看全部

    **Note**：如果用户询问"为什么只显示了部分"，说明他们need完整data
    """
    tools = _get_tools()
    result = tools['data'].get_news_by_date(
        date_query=date_query,
        platforms=platforms,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)



# ==================== 高级dataanalysis工具 ====================

@mcp.tool
async def analyze_topic_trend(
    topic: str,
    analysis_type: str = "trend",
    date_range: Optional[Dict[str, str]] = None,
    granularity: str = "day",
    threshold: float = 3.0,
    time_window: int = 24,
    lookahead_hours: int = 6,
    confidence_threshold: float = 0.7
) -> str:
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
                    - **示例**: {"start": "2025-10-18", "end": "2025-10-25"}
                    - **说明**: AIneed根据用户的自然语言（如"最近7天"）自动计算date范围
                    - **default**: When not specifieddefaultanalysis最近7天
        granularity: time粒度（trend模式），default"day"（仅support day，因为底层data按天聚合）
        threshold: 热度突增倍数阈值（viral模式），default3.0
        time_window: 检测time窗口hour数（viral模式），default24
        lookahead_hours: 预测未来hour数（predict模式），default6
        confidence_threshold: 置信度阈值（predict模式），default0.7

    Returns:
        JSON格式的趋势analysisresult

    **AIuse说明：**
    当用户use相对time表达时（如"最近7天"、"过去一周"、"上个月"），
    AIneed自动计算对应的date范围并传递给 date_range 参数。

    Examples:
        - analyze_topic_trend(topic="人工智能", analysis_type="trend", date_range={"start": "2025-10-18", "end": "2025-10-25"})
        - analyze_topic_trend(topic="特斯拉", analysis_type="lifecycle", date_range={"start": "2025-10-18", "end": "2025-10-25"})
        - analyze_topic_trend(topic="比特币", analysis_type="viral", threshold=3.0)
        - analyze_topic_trend(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_topic_trend_unified(
        topic=topic,
        analysis_type=analysis_type,
        date_range=date_range,
        granularity=granularity,
        threshold=threshold,
        time_window=time_window,
        lookahead_hours=lookahead_hours,
        confidence_threshold=confidence_threshold
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_data_insights(
    insight_type: str = "platform_compare",
    topic: Optional[str] = None,
    date_range: Optional[Dict[str, str]] = None,
    min_frequency: int = 3,
    top_n: int = 20
) -> str:
    """
    统一data洞察analysis工具 - 整合多种dataanalysis模式

    Args:
        insight_type: 洞察类型，optional值：
            - "platform_compare": Platform对比analysis（对比不同Platform对话题的关注度）
            - "platform_activity": Platform活跃度statistics（statistics各Platform发布频率和活跃time）
            - "keyword_cooccur": 关键词共现analysis（analysis关键词同时出现的模式）
        topic: 话题关键词（optional，platform_compare模式适用）
        date_range: **【对象类型】** date范围（optional）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: 必须是对象格式，不能传递整数
        min_frequency: 最小共现频次（keyword_cooccur模式），default3
        top_n: returnTOP Nresult（keyword_cooccur模式），default20

    Returns:
        JSON格式的data洞察analysisresult

    Examples:
        - analyze_data_insights(insight_type="platform_compare", topic="人工智能")
        - analyze_data_insights(insight_type="platform_activity", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_data_insights(insight_type="keyword_cooccur", min_frequency=5, top_n=15)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_data_insights_unified(
        insight_type=insight_type,
        topic=topic,
        date_range=date_range,
        min_frequency=min_frequency,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_sentiment(
    topic: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    limit: int = 50,
    sort_by_weight: bool = True,
    include_url: bool = False
) -> str:
    """
    analysisnews的情感倾向和热度趋势

    Args:
        topic: 话题关键词（optional）
        platforms: List of platform IDs，如 ['zhihu', 'weibo', 'douyin']
                   - When not specified：use config.yaml 中配置的所有Platform
                   - Supported platforms来自 config/config.yaml 的 platforms 配置
                   - 每个Platform都有对应的name字段（如"Zhihu"、"Weibo"），方便AI识别
        date_range: **【对象类型】** date范围（optional）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: 必须是对象格式，不能传递整数
        limit: returnnews数量，default50，最大100
               Note：本工具会对newstitle进行去重（同一title在不同Platform只保留一次），
               因此实际return数量可能少于请求的 limit 值
        sort_by_weight: 是否按热度权重sort，defaultTrue
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的analysisresult，include情感分布、热度趋势和相关news

    **Important：data展示策略**
    - 本工具return完整的analysisresult和newslist
    - **default展示方式**：展示完整的analysisresult（包括所有news）
    - 仅在用户明确要求"总结"或"挑重点"时才进行filter
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_sentiment(
        topic=topic,
        platforms=platforms,
        date_range=date_range,
        limit=limit,
        sort_by_weight=sort_by_weight,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def find_similar_news(
    reference_title: str,
    threshold: float = 0.6,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    查找与指定newstitle相似的其他news

    Args:
        reference_title: newstitle（完整或部分）
        threshold: 相似度阈值，0-1之间，default0.6
                   Note：阈值越高匹配越严格，returnresult越少
        limit: return条数limit，default50，最大100
               Note：实际return数量取决于相似度匹配result，可能少于请求值
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的相似newslist，include相似度分数

    **Important：data展示策略**
    - 本工具return完整的相似newslist
    - **default展示方式**：展示全部return的news（包括相似度分数）
    - 仅在用户明确要求"总结"或"挑重点"时才进行filter
    """
    tools = _get_tools()
    result = tools['analytics'].find_similar_news(
        reference_title=reference_title,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def generate_summary_report(
    report_type: str = "daily",
    date_range: Optional[Dict[str, str]] = None
) -> str:
    """
    每日/每周摘要Generate器 - 自动Generatehot topic摘要report

    Args:
        report_type: report类型（daily/weekly）
        date_range: **【对象类型】** customdate范围（optional）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: 必须是对象格式，不能传递整数

    Returns:
        JSON格式的摘要report，includeMarkdown格式content
    """
    tools = _get_tools()
    result = tools['analytics'].generate_summary_report(
        report_type=report_type,
        date_range=date_range
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 智能检索工具 ====================

@mcp.tool
async def search_news(
    query: str,
    search_mode: str = "keyword",
    date_range: Optional[Dict[str, str]] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    sort_by: str = "relevance",
    threshold: float = 0.6,
    include_url: bool = False
) -> str:
    """
    统一search接口，support多种search模式

    Args:
        query: Search keyword或content片段
        search_mode: search模式，optional值：
            - "keyword": 精确关键词匹配（default，适合search特定话题）
            - "fuzzy": 模糊content匹配（适合searchcontent片段，会过滤相似度低于阈值的result）
            - "entity": 实体名称search（适合search人物/地点/机构）
        date_range: date范围（optional）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **说明**: AIneed根据用户的自然语言（如"最近7天"）自动计算date范围
                    - **default**: When not specifieddefaultquerytoday的news
                    - **Note**: start和endcan相同（表示单日query）
        platforms: List of platform IDs，如 ['zhihu', 'weibo', 'douyin']
                   - When not specified：use config.yaml 中配置的所有Platform
                   - Supported platforms来自 config/config.yaml 的 platforms 配置
                   - 每个Platform都有对应的name字段（如"Zhihu"、"Weibo"），方便AI识别
        limit: return条数limit，default50，最大1000
               Note：实际return数量取决于search匹配result（特别是 fuzzy 模式下会过滤低相似度result）
        sort_by: sort方式，optional值：
            - "relevance": 按相关度sort（default）
            - "weight": 按news权重sort
            - "date": 按datesort
        threshold: 相似度阈值（仅fuzzy模式有效），0-1之间，default0.6
                   Note：阈值越高匹配越严格，returnresult越少
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的searchresult，includetitle、Platform、rank等information

    **Important：data展示策略**
    - 本工具return完整的searchresultlist
    - **default展示方式**：展示全部return的news，无需总结或filter
    - 仅在用户明确要求"总结"或"挑重点"时才进行filter

    **AIuse说明：**
    当用户use相对time表达时（如"最近7天"、"过去一周"、"最近半个月"），
    AIneed自动计算对应的date范围。计算规则：
    - "最近7天" → {"start": "today-6天", "end": "today"}
    - "过去一周" → {"start": "today-6天", "end": "today"}
    - "最近30天" → {"start": "today-29天", "end": "today"}

    Examples:
        - today的news: search_news(query="人工智能")
        - 最近7天: search_news(query="人工智能", date_range={"start": "2025-10-18", "end": "2025-10-25"})
        - 精确date: search_news(query="人工智能", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - 模糊search: search_news(query="特斯拉降价", search_mode="fuzzy", threshold=0.4)
    """
    tools = _get_tools()
    result = tools['search'].search_news_unified(
        query=query,
        search_mode=search_mode,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        sort_by=sort_by,
        threshold=threshold,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def search_related_news_history(
    reference_text: str,
    time_preset: str = "yesterday",
    threshold: float = 0.4,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    基于种子news，在historydata中search相关news

    Args:
        reference_text: 参考newstitle（完整或部分）
        time_preset: time范围预设值，optional：
            - "yesterday": yesterday
            - "last_week": 上周 (7天)
            - "last_month": 上个月 (30天)
            - "custom": customdate范围（need提供 start_date 和 end_date）
        threshold: 相关性阈值，0-1之间，default0.4
                   Note：综合相似度计算（70%关键词重合 + 30%文本相似度）
                   阈值越高匹配越严格，returnresult越少
        limit: return条数limit，default50，最大100
               Note：实际return数量取决于相关性匹配result，可能少于请求值
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的相关newslist，include相关性分数和time分布

    **Important：data展示策略**
    - 本工具return完整的相关newslist
    - **default展示方式**：展示全部return的news（包括相关性分数）
    - 仅在用户明确要求"总结"或"挑重点"时才进行filter
    """
    tools = _get_tools()
    result = tools['search'].search_related_news_history(
        reference_text=reference_text,
        time_preset=time_preset,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 配置与系统管理工具 ====================

@mcp.tool
async def get_current_config(
    section: str = "all"
) -> str:
    """
    Getcurrent系统配置

    Args:
        section: 配置节，optional值：
            - "all": 所有配置（default）
            - "crawler": 爬虫配置
            - "push": 推送配置
            - "keywords": 关键词配置
            - "weights": 权重配置

    Returns:
        JSON格式的配置information
    """
    tools = _get_tools()
    result = tools['config'].get_current_config(section=section)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_system_status() -> str:
    """
    Get系统运行状态和健康Checkinformation

    return系统版本、datastatistics、缓存状态等information

    Returns:
        JSON格式的系统状态information
    """
    tools = _get_tools()
    result = tools['system'].get_system_status()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def trigger_crawl(
    platforms: Optional[List[str]] = None,
    save_to_local: bool = False,
    include_url: bool = False
) -> str:
    """
    手动触发一次爬取任务（optional持久化）

    Args:
        platforms: 指定List of platform IDs，如 ['zhihu', 'weibo', 'douyin']
                   - When not specified：use config.yaml 中配置的所有Platform
                   - Supported platforms来自 config/config.yaml 的 platforms 配置
                   - 每个Platform都有对应的name字段（如"Zhihu"、"Weibo"），方便AI识别
                   - Note：failed的Platform会在returnresult的 failed_platforms 字段中列出
        save_to_local: 是否Save到本地 output directory，default False
        include_url: 是否includeURLlink，defaultFalse（节省token）

    Returns:
        JSON格式的任务状态information，include：
        - platforms: successfully爬取的Platformlist
        - failed_platforms: failed的Platformlist（如有）
        - total_news: 爬取的news总数
        - data: newsdata

    Examples:
        - 临时爬取: trigger_crawl(platforms=['zhihu'])
        - 爬取并Save: trigger_crawl(platforms=['weibo'], save_to_local=True)
        - usedefaultPlatform: trigger_crawl()  # 爬取config.yaml中配置的所有Platform
    """
    tools = _get_tools()
    result = tools['system'].trigger_crawl(platforms=platforms, save_to_local=save_to_local, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Start入口 ====================

def run_server(
    project_root: Optional[str] = None,
    transport: str = 'stdio',
    host: str = '0.0.0.0',
    port: int = 3333
):
    """
    Start MCP 服务器

    Args:
        project_root: 项目根directorypath
        transport: 传输模式，'stdio' 或 'http'
        host: HTTP模式的监听地址，default 0.0.0.0
        port: HTTP模式的监听端口，default 3333
    """
    # Initialize工具实例
    _get_tools(project_root)

    # 打印Startinformation
    print()
    print("=" * 60)
    print("  TrendRadar MCP Server - FastMCP 2.0")
    print("=" * 60)
    print(f"  传输模式: {transport.upper()}")

    if transport == 'stdio':
        print("  协议: MCP over stdio (标准inputoutput)")
        print("  说明: 通过标准inputoutput与 MCP 客户端通信")
    elif transport == 'http':
        print(f"  监听地址: http://{host}:{port}")
        print(f"  HTTP端点: http://{host}:{port}/mcp")
        print("  协议: MCP over HTTP (生产环境)")

    if project_root:
        print(f"  项目directory: {project_root}")
    else:
        print("  项目directory: currentdirectory")

    print()
    print("  已注册的工具:")
    print("    === 基础dataquery（P0核心）===")
    print("    1. get_latest_news        - Getlatestnews")
    print("    2. get_news_by_date       - 按datequerynews（support自然语言）")
    print("    3. get_trending_topics    - Get趋势话题")
    print()
    print("    === 智能检索工具 ===")
    print("    4. search_news                  - 统一newssearch（关键词/模糊/实体）")
    print("    5. search_related_news_history  - history相关news检索")
    print()
    print("    === 高级dataanalysis ===")
    print("    6. analyze_topic_trend      - 统一话题趋势analysis（热度/生命周期/爆火/预测）")
    print("    7. analyze_data_insights    - 统一data洞察analysis（Platform对比/活跃度/关键词共现）")
    print("    8. analyze_sentiment        - 情感倾向analysis")
    print("    9. find_similar_news        - 相似news查找")
    print("    10. generate_summary_report - 每日/每周摘要Generate")
    print()
    print("    === 配置与系统管理 ===")
    print("    11. get_current_config      - Getcurrent系统配置")
    print("    12. get_system_status       - Get系统运行状态")
    print("    13. trigger_crawl           - 手动触发爬取任务")
    print("=" * 60)
    print()

    # 根据传输模式运行服务器
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'http':
        # HTTP 模式（生产推荐）
        mcp.run(
            transport='http',
            host=host,
            port=port,
            path='/mcp'  # HTTP 端点path
        )
    else:
        raise ValueError(f"不support的传输模式: {transport}")


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='TrendRadar MCP Server - newshot topic聚合 MCP 工具服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
use示例:
  # STDIO 模式（用于 Cherry Studio）
  uv run python mcp_server/server.py

  # HTTP 模式（适合远程访问）
  uv run python mcp_server/server.py --transport http --port 3333

Cherry Studio 配置示例:
  设置 > MCP Servers > 添加服务器
  - 名称: TrendRadar
  - 类型: STDIO
  - 命令: [UV的完整path]
  - 参数: --directory [项目path] run python mcp_server/server.py

详细配置教程请查看: README-Cherry-Studio.md
        """
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='传输模式：stdio (default) 或 http (生产环境)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='HTTP模式的监听地址，default 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3333,
        help='HTTP模式的监听端口，default 3333'
    )
    parser.add_argument(
        '--project-root',
        help='项目根directorypath'
    )

    args = parser.parse_args()

    run_server(
        project_root=args.project_root,
        transport=args.transport,
        host=args.host,
        port=args.port
    )
