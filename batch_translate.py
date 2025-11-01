#!/usr/bin/env python3
"""
Comprehensive batch translation script
Translates Chinese to English in Python files, comments, docstrings, and user messages
"""

import os
import re
from pathlib import Path

# Comprehensive translation dictionary
TRANSLATIONS = {
    # Configuration and setup
    "配置管理": "Configuration Management",
    "配置文件": "configuration file",
    "加载配置文件": "Load configuration file",
    "配置文件加载成功": "Configuration file loaded successfully",
    "不存在": "does not exist",
    "构建配置": "Build configuration",
    "通知渠道配置（环境变量优先）": "Notification channel configuration (environment variables take priority)",
    "邮件配置": "Email configuration",
    
    # Comments
    "SMTP邮件配置": "SMTP Email Configuration",
    "QQ邮箱": "QQ Mail",
    "网易邮箱": "NetEase Mail",
    "新浪邮箱": "Sina Mail",
    "搜狐邮箱": "Sohu Mail",
    
    # Platform names (keep Chinese names in Chinese but translate descriptions)
    "知乎": "Zhihu",
    "微博": "Weibo",
    "钉钉": "DingTalk",
    "飞书": "Feishu",
    "企业微信": "WeCom",
    
    # Common function/method descriptions
    "获取": "Get",
    "加载": "Load",
    "保存": "Save",
    "删除": "Delete",
    "更新": "Update",
    "创建": "Create",
    "检查": "Check",
    "验证": "Validate",
    "解析": "Parse",
    "发送": "Send",
    "接收": "Receive",
    "处理": "Process",
    "生成": "Generate",
    "执行": "Execute",
    "初始化": "Initialize",
    "启动": "Start",
    "停止": "Stop",
    "重试": "Retry",
    "失败": "failed",
    "成功": "successfully",
    
    # Data and results
    "数据": "data",
    "结果": "result",
    "列表": "list",
    "字典": "dictionary",
    "文件": "file",
    "目录": "directory",
    "路径": "path",
    "内容": "content",
    "信息": "information",
    "消息": "message",
    "通知": "notification",
    "报告": "report",
    "日志": "log",
    "记录": "record",
    "统计": "statistics",
    "分析": "analysis",
    "查询": "query",
    "搜索": "search",
    "筛选": "filter",
    "排序": "sort",
    "排名": "rank",
    "热点": "hot topic",
    "新闻": "news",
    "标题": "title",
    "链接": "link",
    "URL": "URL",
    
    # Time and date
    "今天": "today",
    "昨天": "yesterday",
    "前天": "the day before yesterday",
    "最新": "latest",
    "当前": "current",
    "历史": "history",
    "时间": "time",
    "日期": "date",
    "小时": "hour",
    "分钟": "minute",
    "秒": "second",
    
    # Status and results  
    "启用": "enabled",
    "禁用": "disabled",
    "开启": "enabled",
    "关闭": "disabled",
    "正常": "normal",
    "异常": "abnormal",
    "错误": "error",
    "警告": "warning",
    "提示": "hint",
    "注意": "Note",
    "重要": "Important",
    "可选": "optional",
    "必填": "required",
    "默认": "default",
    "自定义": "custom",
    
    # Common phrases
    "不指定时": "When not specified",
    "可以": "can",
    "需要": "need",
    "支持": "support",
    "不支持": "not supported",
    "允许": "allow",
    "禁止": "prohibit",
    "包含": "include",
    "排除": "exclude",
    "限制": "limit",
    "超过": "exceed",
    "小于": "less than",
    "大于": "greater than",
    "等于": "equal to",
    "使用": "use",
    "返回": "return",
    "输入": "input",
    "输出": "output",
    
    # Error messages
    "请检查": "Please check",
    "请使用": "Please use",
    "请提供": "Please provide",
    "请稍后重试": "Please retry later",
    "不能为空": "cannot be empty",
    "格式错误": "format error",
    "参数错误": "parameter error",
    "配置错误": "configuration error",
    "网络错误": "network error",
    "文件不存在": "file does not exist",
    "目录不存在": "directory does not exist",
    
    # User feedback
    "请等待": "Please wait",
    "正在": "In progress",
    "已完成": "completed",
    "已取消": "canceled",
    "已跳过": "skipped",
}

def translate_line(line):
    """Translate a single line"""
    result = line
    for chinese, english in TRANSLATIONS.items():
        if chinese in result:
            result = result.replace(chinese, english)
    return result

def translate_file(filepath):
    """Translate a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Process line by line
        translated_lines = []
        changed = False
        for line in lines:
            translated = translate_line(line)
            translated_lines.append(translated)
            if translated != line:
                changed = True
        
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(translated_lines)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function"""
    project_root = Path("/home/engine/project")
    
    # Files to translate
    files_to_process = []
    
    # Python files in mcp_server
    files_to_process.extend(list((project_root / "mcp_server").rglob("*.py")))
    
    # Main.py
    main_py = project_root / "main.py"
    if main_py.exists():
        files_to_process.append(main_py)
    
    # Docker management script
    docker_manage = project_root / "docker" / "manage.py"
    if docker_manage.exists():
        files_to_process.append(docker_manage)
    
    print(f"Processing {len(files_to_process)} Python files...")
    
    translated = 0
    for filepath in files_to_process:
        if translate_file(filepath):
            print(f"✓ {filepath.relative_to(project_root)}")
            translated += 1
        else:
            print(f"- {filepath.relative_to(project_root)}")
    
    print(f"\nTranslated {translated}/{len(files_to_process)} files")

if __name__ == "__main__":
    main()
