#!/usr/bin/env python3
import re

# Read the file
with open('/home/engine/project/mcp_server/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extended translations for server.py
replacements = [
    ("不指定时：使用 config.yaml 中配置的所有Platform", "When not specified: use all platforms configured in config.yaml"),
    ("Supported platforms来自 config/config.yaml 的 platforms 配置", "Supported platforms come from the platforms configuration in config/config.yaml"),
    ("每个Platform都有对应的name字段（如"知乎"、"微博"），方便AI识别", "Each platform has a corresponding name field (such as 'Zhihu', 'Weibo') for easy AI recognition"),
    ("返回条数限制，默认50，最大1000", "Return limit, default 50, maximum 1000"),
    ("注意：实际返回数量可能少于请求值，取决于当前可用的新闻总数", "Note: Actual return count may be less than requested, depending on total available news"),
    ("注意：实际返回数量可能少于请求值，取决于指定日期的新闻总数", "Note: Actual return count may be less than requested, depending on total news for the specified date"),
    ("是否包含URL链接，默认False（节省token）", "Whether to include URL links, default False (saves tokens)"),
    ("JSON格式的新闻列表", "JSON format news list"),
    ("JSON格式的新闻列表，包含标题、Platform、排名等信息", "JSON format news list, including title, platform, rank and other information"),
    ("JSON格式的关注词频率统计列表", "JSON format keyword frequency statistics list"),
    
    ("重要：数据展示建议", "Important: Data Display Recommendations"),
    ("本工具会返回完整的新闻列表（通常50条）给你。但请注意：", "This tool returns a complete news list (usually 50 items) to you. But please note:"),
    ("工具返回", "Tool returns"),
    ("完整的50条数据", "Complete 50 items of data"),
    ("建议展示", "Display recommendation"),
    ("向用户展示全部数据，除非用户明确要求总结", "Display all data to the user unless they explicitly request a summary"),
    ("用户期望", "User expectation"),
    ("用户可能需要完整数据，请谨慎总结", "Users may need complete data, be cautious with summaries"),
    
    ("何时可以总结", "When to summarize"),
    ("用户明确说"给我总结一下"或"挑重点说"", 'User explicitly says "give me a summary" or "highlight the key points"'),
    ("数据量超过100条时，可先展示部分并询问是否查看全部", "When data exceeds 100 items, display part first and ask if they want to see all"),
    ("如果用户询问"为什么只显示了部分"，说明他们需要完整数据", 'If user asks "why only showing part", it means they need complete data'),
    
    ("获取最新一批爬取的新闻数据，快速了解当前热点", "Get the latest batch of crawled news data to quickly understand current hot topics"),
    ("获取个人关注词的新闻出现频率统计（基于 config/frequency_words.txt）", "Get keyword frequency statistics for personally monitored words (based on config/frequency_words.txt)"),
    ("注意：本工具不是自动提取新闻热点，而是统计你在 config/frequency_words.txt 中", "Note: This tool does not automatically extract news hotspots, but counts the frequency of your personally monitored words in"),
    ("设置的个人关注词在新闻中出现的频率。你可以自定义这个关注词列表。", "config/frequency_words.txt appearing in the news. You can customize this keyword list."),
    ("返回TOP N关注词，默认10", "Return TOP N monitored words, default 10"),
    ("模式选择", "Mode selection"),
    ("当日累计数据统计", "Daily cumulative data statistics"),
    ("最新一批数据统计（默认）", "Latest batch data statistics (default)"),
    
    ("获取指定日期的新闻数据，用于历史数据分析和对比", "Get news data for a specified date, for historical data analysis and comparison"),
    ("日期查询，可选格式:", "Date query, optional formats:"),
    ("自然语言", "Natural language"),
    ("标准日期", "Standard date"),
    ("Default value:", "Default value:"),
    ("节省token", "saves tokens"),
    
    ("数据查询工具", "Data Query Tools"),
    ("数据分析工具", "Data Analysis Tools"),
    ("搜索工具", "Search Tools"),
    ("配置管理工具", "Configuration Management Tools"),
    ("系统管理工具", "System Management Tools"),
    
    # More specific translations
    ("获取", "Get"),
    ("返回", "Returns"),
    ("默认", "Default"),
    ("列表", "list"),
]

# Apply replacements
for chinese, english in replacements:
    content = content.replace(chinese, english)

# Write back
with open('/home/engine/project/mcp_server/server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Translation complete for server.py")
