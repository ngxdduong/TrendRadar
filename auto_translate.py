#!/usr/bin/env python3
"""
Automated translation script for TrendRadar project
Translates Chinese comments and strings to English
"""

import re
import os
from pathlib import Path

# Translation dictionary - maps Chinese phrases to English
TRANSLATIONS = {
    # Common docstrings and comments
    "提供基于MCP协议的新闻聚合数据查询和系统管理接口": "Provides news aggregation data query and system management interface based on MCP protocol",
    "工具类模块": "Utility Module",
    "提供参数验证、错误处理等辅助功能": "Provides auxiliary functions such as parameter validation and error handling",
    "服务层模块": "Service Layer Module", 
    "提供数据访问、缓存、解析等核心服务": "Provides core services such as data access, caching, and parsing",
    "MCP 工具模块": "MCP Tools Module",
    "包含所有MCP工具的实现": "Contains all MCP tool implementations",
    "自定义错误类": "Custom Error Classes",
    "定义MCP Server使用的所有自定义异常类型": "Defines all custom exception types used by MCP Server",
    "参数验证工具": "Parameter Validation Tool",
    "提供统一的参数验证功能": "Provides unified parameter validation functions",
    "日期解析工具": "Date Parsing Tool",
    "支持多种自然语言日期格式解析，包括相对日期和绝对日期": "Supports parsing of multiple natural language date formats, including relative and absolute dates",
    
    # Error class translations
    "MCP工具错误基类": "Base class for MCP tool errors",
    "数据不存在错误": "Data not found error",
    "参数无效错误": "Invalid parameter error",
    "配置错误": "Configuration error",
    "平台不支持错误": "Platform not supported error",
    "爬取任务错误": "Crawl task error",
    "文件解析错误": "File parse error",
    "转换为字典格式": "Convert to dictionary format",
    
    # Common method docstrings  
    "验证平台列表": "Validate platform list",
    "验证数量限制参数": "Validate quantity limit parameter",
    "验证日期格式": "Validate date format",
    "验证日期范围": "Validate date range",
    "验证关键词": "Validate keyword",
    "验证TOP N参数": "Validate TOP N parameter",
    "验证模式参数": "Validate mode parameter",
    "验证配置节参数": "Validate config section parameter",
    "验证并解析日期查询字符串": "Validate and parse date query string",
    "解析日期查询字符串": "Parse date query string",
    "日期解析器类": "Date parser class",
    
    # Parameter descriptions
    "平台ID列表": "List of platform IDs",
    "验证后的平台列表": "Validated platform list",
    "限制数量": "Limit quantity",
    "默认值": "Default value",
    "最大限制": "Maximum limit",
    "验证后的限制值": "Validated limit value",
    "日期字符串": "Date string",
    "日期范围字典": "Date range dictionary",
    "搜索关键词": "Search keyword",
    "处理后的关键词": "Processed keyword",
    "模式字符串": "Mode string",
    "有效模式列表": "Valid modes list",
    "默认模式": "Default mode",
    "验证后的模式": "Validated mode",
    "配置节名称": "Config section name",
    "验证后的配置节": "Validated config section",
    "日期查询字符串": "Date query string",
    "是否允许未来日期": "Whether to allow future dates",
    "允许查询的最大天数": "Maximum days allowed for query",
    "解析后的datetime对象": "Parsed datetime object",
    "datetime对象": "datetime object",
    "元组，或 None": "tuple, or None",
    
    # Error messages and suggestions
    "平台不支持": "Platform not supported",
    "参数无效": "Invalid parameter",
    "日期格式错误": "Date format error",
    "日期范围无效": "Invalid date range",
    "关键词无效": "Invalid keyword",
    "模式无效": "Invalid mode",
    "配置节无效": "Invalid config section",
    "日期查询无效": "Invalid date query",
    
    "请检查日期范围或等待爬取任务完成": "Please check the date range or wait for the crawl task to complete",
    "请检查参数格式是否正确": "Please check if the parameter format is correct",
    "请检查配置文件是否正确": "Please check if the configuration file is correct",
    "请稍后重试或查看日志": "Please retry later or check the logs",
    "请使用 YYYY-MM-DD 格式，例如": "Please use YYYY-MM-DD format, for example",
    "请使用更简洁的关键词": "Please use more concise keywords",
    "请使用分页或降低limit值": "Please use pagination or reduce limit value",
    "请提供日期查询，如：今天、昨天": "Please provide date query, such as: today, yesterday",
    
    "platforms 参数必须是列表类型": "platforms parameter must be a list type",
    "limit 参数必须是整数类型": "limit parameter must be an integer type",
    "mode 必须是字符串类型": "mode must be a string type",
    "keyword 必须是字符串类型": "keyword must be a string type",
    "date_range 必须是字典类型": "date_range must be a dictionary type",
    
    "limit 必须大于0": "limit must be greater than 0",
    "limit 不能超过": "limit cannot exceed",
    "keyword 不能为空": "keyword cannot be empty",
    "keyword 不能为空白字符": "keyword cannot be blank characters",
    "keyword 长度不能超过100个字符": "keyword length cannot exceed 100 characters",
    "date_range 必须包含 start 和 end 字段": "date_range must contain start and end fields",
    "开始日期不能晚于结束日期": "Start date cannot be later than end date",
    "不允许查询未来日期": "Future date queries not allowed",
    "日期查询字符串不能为空": "Date query string cannot be empty",
    "当前日期": "Current date",
    "当前可用数据范围": "Currently available data range",
    
    "不支持的平台": "Unsupported platforms",
    "支持的平台（来自config.yaml）": "Supported platforms (from config.yaml)",
    "支持的平台": "Supported platforms",
    "支持的模式": "Supported modes",
    "无效的模式": "Invalid mode",
    "例如": "For example",
    
    # Comments
    "返回配置文件中的平台列表（用户的默认配置）": "Return platform list from config file (user's default configuration)",
    "空列表时，返回配置文件中的平台列表": "When empty list, return platform list from config file",
    "如果配置加载失败（supported_platforms为空），允许所有平台通过": "If config loading fails (supported_platforms is empty), allow all platforms to pass",
    "验证每个平台是否在配置中": "Verify each platform is in configuration",
    "检查日期是否在未来": "Check if date is in the future",
    "获取可用日期范围提示": "Get available date range hint",
    "获取 config.yaml 路径（相对于当前文件）": "Get config.yaml path (relative to current file)",
    "降级方案：返回空列表，允许所有平台": "Fallback: return empty list, allow all platforms",
    "使用DateParser解析日期": "Use DateParser to parse date",
    "验证日期不在未来": "Validate date is not in the future",
    "验证日期不太久远": "Validate date is not too old",
    
    "警告：无法加载平台配置": "Warning: Unable to load platform configuration",
    "警告：平台配置未加载，跳过平台验证": "Warning: Platform configuration not loaded, skipping platform validation",
    "至": "to",
    "无可用数据": "No data available",
    "未知（请检查 output 目录）": "Unknown (please check output directory)",
    
    # Platform and date-related
    "平台": "Platform",
    "不受支持": "is not supported",
    "解析文件": "Failed to parse file",
    "失败": "failed",
    
    # Chinese date/time words
    "今天": "today",
    "昨天": "yesterday",
    "前天": "the day before yesterday",
    "大前天": "three days ago",
    
    # Config related  
    "配置文件": "configuration file",
    "不存在": "does not exist",
    "加载成功": "loaded successfully",
    "加载配置文件": "Load configuration file",
    "配置文件加载成功": "Configuration file loaded successfully",
}

def translate_text(text):
    """Replace Chinese text with English translations"""
    result = text
    for chinese, english in sorted(TRANSLATIONS.items(), key=lambda x: -len(x[0])):
        result = result.replace(chinese, english)
    return result

def process_file(filepath):
    """Process a single file and translate Chinese to English"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        content = translate_text(content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Translated: {filepath}")
            return True
        else:
            print(f"- No changes: {filepath}")
            return False
    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all Python files"""
    project_root = Path("/home/engine/project")
    mcp_server = project_root / "mcp_server"
    
    files_to_process = []
    for pattern in ["**/*.py"]:
        files_to_process.extend(mcp_server.glob(pattern))
    
    print(f"Found {len(files_to_process)} Python files to process\n")
    
    translated_count = 0
    for filepath in sorted(files_to_process):
        if process_file(filepath):
            translated_count += 1
    
    print(f"\n{'='*60}")
    print(f"Translation complete!")
    print(f"Files translated: {translated_count}/{len(files_to_process)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
