#!/usr/bin/env python3
"""
Translation helper script
This script contains Chinese to English translations mapping
"""

# Common translations for validators.py and other files
TRANSLATIONS = {
    # validators.py
    "验证平台列表": "Validate platform list",
    "平台ID列表，None表示使用 config.yaml 中配置的所有平台": "List of platform IDs, None means use all platforms configured in config.yaml",
    "验证后的平台列表": "Validated platform list",
    "平台不支持": "Platform not supported",
    "platforms 参数必须是列表类型": "platforms parameter must be a list type",
    "返回配置文件中的平台列表（用户的默认配置）": "Return platform list from config file (user's default configuration)",
    "空列表时，返回配置文件中的平台列表": "When empty list, return platform list from config file",
    "如果配置加载失败（supported_platforms为空），允许所有平台通过": "If config loading fails (supported_platforms is empty), allow all platforms to pass",
    "警告：平台配置未加载，跳过平台验证": "Warning: Platform configuration not loaded, skipping platform validation",
    "验证每个平台是否在配置中": "Verify each platform is in configuration",
    "不支持的平台": "Unsupported platforms",
    "支持的平台（来自config.yaml）": "Supported platforms (from config.yaml)",
    
    # Common error messages
    "参数无效": "Invalid parameter",
    "配置文件": "configuration file",
    "不存在": "does not exist",
    "加载成功": "loaded successfully",
    
    # Date related
    "日期格式错误": "Date format error",
    "请使用 YYYY-MM-DD 格式，例如": "Please use YYYY-MM-DD format, for example",
    "验证日期范围": "Validate date range",
    "日期范围字典": "Date range dictionary",
    "元组，或 None": "tuple, or None",
    "日期范围无效": "Invalid date range",
    "date_range 必须是字典类型": "date_range must be a dictionary type",
    "date_range 必须包含 start 和 end 字段": "date_range must contain start and end fields",
    "例如": "For example",
    "开始日期不能晚于结束日期": "Start date cannot be later than end date",
    "检查日期是否在未来": "Check if date is in the future",
    "获取可用日期范围提示": "Get available date range hint",
    "至": "to",
    "无可用数据": "No data available",
    "未知（请检查 output 目录）": "Unknown (please check output directory)",
    "不允许查询未来日期": "Future date queries not allowed",
    "当前日期": "Current date",
    "当前可用数据范围": "Currently available data range",
    
    # Keyword related
    "验证关键词": "Validate keyword",
    "搜索关键词": "Search keyword",
    "处理后的关键词": "Processed keyword",
    "关键词无效": "Invalid keyword",
    "keyword 不能为空": "keyword cannot be empty",
    "keyword 必须是字符串类型": "keyword must be a string type",
    "keyword 不能为空白字符": "keyword cannot be blank characters",
    "keyword 长度不能超过100个字符": "keyword length cannot exceed 100 characters",
    "请使用更简洁的关键词": "Please use more concise keywords",
    
    # Limit/validation related
    "验证数量限制参数": "Validate quantity limit parameter",
    "限制数量": "Limit quantity",
    "默认值": "Default value",
    "最大限制": "Maximum limit",
    "验证后的限制值": "Validated limit value",
    "limit 参数必须是整数类型": "limit parameter must be an integer type",
    "limit 必须大于0": "limit must be greater than 0",
    "limit 不能超过": "limit cannot exceed",
    "请使用分页或降低limit值": "Please use pagination or reduce limit value",
    
    # Mode/config related
    "验证模式参数": "Validate mode parameter",
    "模式字符串": "Mode string",
    "有效模式列表": "Valid modes list",
    "默认模式": "Default mode",
    "验证后的模式": "Validated mode",
    "模式无效": "Invalid mode",
    "mode 必须是字符串类型": "mode must be a string type",
    "无效的模式": "Invalid mode",
    "支持的模式": "Supported modes",
    "验证配置节参数": "Validate config section parameter",
    "配置节名称": "Config section name",
    "验证后的配置节": "Validated config section",
    "配置节无效": "Invalid config section",
    
    # Date query
    "验证并解析日期查询字符串": "Validate and parse date query string",
    "日期查询字符串": "Date query string",
    "是否允许未来日期": "Whether to allow future dates",
    "允许查询的最大天数": "Maximum days allowed for query",
    "解析后的datetime对象": "Parsed datetime object",
    "日期查询无效": "Invalid date query",
    "日期查询字符串不能为空": "Date query string cannot be empty",
    "请提供日期查询，如：今天、昨天、2025-10-10": "Please provide date query, such as: today, yesterday, 2025-10-10",
    
    # Date parser
    "日期解析工具": "Date parsing tool",
    "支持多种自然语言日期格式解析，包括相对日期和绝对日期。": "Supports parsing of multiple natural language date formats, including relative and absolute dates.",
    "日期解析器类": "Date parser class",
    "解析日期查询字符串": "Parse date query string",
    "今天": "today",
    "昨天": "yesterday",
    "前天": "the day before yesterday",
    "大前天": "three days ago",
    
    # Service layer
    "服务层模块": "Service layer module",
    "提供数据访问、缓存、解析等核心服务。": "Provides core services such as data access, caching, and parsing.",
    
    # Tools
    "MCP 工具模块": "MCP tools module",
    "包含所有MCP工具的实现。": "Contains all MCP tool implementations.",
    
    # Utils
    "工具类模块": "Utility module",
    "提供参数验证、错误处理等辅助功能。": "Provides auxiliary functions such as parameter validation and error handling.",
    
    # Errors
    "自定义错误类": "Custom error classes",
    "定义MCP Server使用的所有自定义异常类型。": "Defines all custom exception types used by MCP Server.",
    "MCP工具错误基类": "Base class for MCP tool errors",
    "转换为字典格式": "Convert to dictionary format",
    "数据不存在错误": "Data not found error",
    "请检查日期范围或等待爬取任务完成": "Please check the date range or wait for the crawl task to complete",
    "参数无效错误": "Invalid parameter error",
    "请检查参数格式是否正确": "Please check if the parameter format is correct",
    "配置错误": "Configuration error",
    "请检查配置文件是否正确": "Please check if the configuration file is correct",
    "平台不支持错误": "Platform not supported error",
    "平台": "Platform",
    "不受支持": "is not supported",
    "支持的平台": "Supported platforms",
    "爬取任务错误": "Crawl task error",
    "请稍后重试或查看日志": "Please retry later or check the logs",
    "文件解析错误": "File parse error",
    "解析文件": "Failed to parse file",
    "失败": "failed",
}

if __name__ == "__main__":
    print("Translation helper loaded")
    print(f"Total translations: {len(TRANSLATIONS)}")
