#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
news爬虫容器管理工具 - supercronic
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(cmd, shell=True, capture_output=True):
    """Execute系统命令"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture_output, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def manual_run():
    """手动Execute一次爬虫"""
    print("🔄 手动Execute爬虫...")
    try:
        result = subprocess.run(
            ["python", "main.py"], cwd="/app", capture_output=False, text=True
        )
        if result.returncode == 0:
            print("✅ Execute完成")
        else:
            print(f"❌ Executefailed，退出码: {result.returncode}")
    except Exception as e:
        print(f"❌ Execute出错: {e}")


def parse_cron_schedule(cron_expr):
    """Parsecron表达式并return人类可读的描述"""
    if not cron_expr or cron_expr == "未设置":
        return "未设置"
    
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return f"原始表达式: {cron_expr}"
        
        minute, hour, day, month, weekday = parts
        
        # analysisminute
        if minute == "*":
            minute_desc = "每minute"
        elif minute.startswith("*/"):
            interval = minute[2:]
            minute_desc = f"每{interval}minute"
        elif "," in minute:
            minute_desc = f"在第{minute}minute"
        else:
            minute_desc = f"在第{minute}minute"
        
        # analysishour
        if hour == "*":
            hour_desc = "每hour"
        elif hour.startswith("*/"):
            interval = hour[2:]
            hour_desc = f"每{interval}hour"
        elif "," in hour:
            hour_desc = f"在{hour}点"
        else:
            hour_desc = f"在{hour}点"
        
        # analysisdate
        if day == "*":
            day_desc = "每天"
        elif day.startswith("*/"):
            interval = day[2:]
            day_desc = f"每{interval}天"
        else:
            day_desc = f"每月{day}号"
        
        # analysis月份
        if month == "*":
            month_desc = "每月"
        else:
            month_desc = f"在{month}月"
        
        # analysis星期
        weekday_names = {
            "0": "周日", "1": "周一", "2": "周二", "3": "周三", 
            "4": "周四", "5": "周五", "6": "周六", "7": "周日"
        }
        if weekday == "*":
            weekday_desc = ""
        else:
            weekday_desc = f"在{weekday_names.get(weekday, weekday)}"
        
        # 组合描述
        if minute.startswith("*/") and hour == "*" and day == "*" and month == "*" and weekday == "*":
            # 简单的间隔模式，如 */30 * * * *
            return f"每{minute[2:]}minuteExecute一次"
        elif hour != "*" and minute != "*" and day == "*" and month == "*" and weekday == "*":
            # 每天特定time，如 0 9 * * *
            return f"每天{hour}:{minute.zfill(2)}Execute"
        elif weekday != "*" and day == "*":
            # 每周特定time
            return f"{weekday_desc}{hour}:{minute.zfill(2)}Execute"
        else:
            # 复杂模式，显示详细information
            desc_parts = [part for part in [month_desc, day_desc, weekday_desc, hour_desc, minute_desc] if part and part != "每月" and part != "每天" and part != "每hour"]
            if desc_parts:
                return " ".join(desc_parts) + "Execute"
            else:
                return f"复杂表达式: {cron_expr}"
    
    except Exception as e:
        return f"Parsefailed: {cron_expr}"


def show_status():
    """显示容器状态"""
    print("📊 容器状态:")

    # Check PID 1 状态
    supercronic_is_pid1 = False
    pid1_cmdline = ""
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 PID 1 进程: {pid1_cmdline}")
        
        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ supercronic 正确运行为 PID 1")
            supercronic_is_pid1 = True
        else:
            print("  ❌ PID 1 不是 supercronic")
            print(f"  📋 实际的 PID 1: {pid1_cmdline}")
    except Exception as e:
        print(f"  ❌ 无法读取 PID 1 information: {e}")

    # Check环境变量
    cron_schedule = os.environ.get("CRON_SCHEDULE", "未设置")
    run_mode = os.environ.get("RUN_MODE", "未设置")
    immediate_run = os.environ.get("IMMEDIATE_RUN", "未设置")
    
    print(f"  ⚙️ 运行配置:")
    print(f"    CRON_SCHEDULE: {cron_schedule}")
    
    # Parse并显示cron表达式的含义
    cron_description = parse_cron_schedule(cron_schedule)
    print(f"    ⏰ Execute频率: {cron_description}")
    
    print(f"    RUN_MODE: {run_mode}")
    print(f"    IMMEDIATE_RUN: {immediate_run}")

    # Checkconfiguration file
    config_files = ["/app/config/config.yaml", "/app/config/frequency_words.txt"]
    print("  📁 configuration file:")
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"    ✅ {Path(file_path).name}")
        else:
            print(f"    ❌ {Path(file_path).name} 缺失")

    # Check关键file
    key_files = [
        ("/usr/local/bin/supercronic-linux-amd64", "supercronic二进制file"),
        ("/usr/local/bin/supercronic", "supercronic软link"),
        ("/tmp/crontab", "crontabfile"),
        ("/entrypoint.sh", "Start脚本")
    ]
    
    print("  📂 关键fileCheck:")
    for file_path, description in key_files:
        if Path(file_path).exists():
            print(f"    ✅ {description}: 存在")
            # 对于crontabfile，显示content
            if file_path == "/tmp/crontab":
                try:
                    with open(file_path, 'r') as f:
                        crontab_content = f.read().strip()
                        print(f"         content: {crontab_content}")
                except:
                    pass
        else:
            print(f"    ❌ {description}: does not exist")

    # Check容器运行time
    print("  ⏱️ 容器timeinformation:")
    try:
        # Check PID 1 的Starttime
        with open('/proc/1/stat', 'r') as f:
            stat_content = f.read().strip().split()
            if len(stat_content) >= 22:
                # starttime 是第22个字段（索引21）
                starttime_ticks = int(stat_content[21])
                
                # 读取系统Starttime
                with open('/proc/stat', 'r') as stat_f:
                    for line in stat_f:
                        if line.startswith('btime'):
                            boot_time = int(line.split()[1])
                            break
                    else:
                        boot_time = 0
                
                # 读取系统时钟频率
                clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                
                if boot_time > 0:
                    pid1_start_time = boot_time + (starttime_ticks / clock_ticks)
                    current_time = time.time()
                    uptime_seconds = int(current_time - pid1_start_time)
                    uptime_minutes = uptime_seconds // 60
                    uptime_hours = uptime_minutes // 60
                    
                    if uptime_hours > 0:
                        print(f"    PID 1 运行time: {uptime_hours} hour {uptime_minutes % 60} minute")
                    else:
                        print(f"    PID 1 运行time: {uptime_minutes} minute ({uptime_seconds} second)")
                else:
                    print(f"    PID 1 运行time: 无法精确计算")
            else:
                print("    ❌ 无法Parse PID 1 statisticsinformation")
    except Exception as e:
        print(f"    ❌ timeCheckfailed: {e}")

    # 状态总结和建议
    print("  📊 状态总结:")
    if supercronic_is_pid1:
        print("    ✅ supercronic 正确运行为 PID 1")
        print("    ✅ 定时任务应该normal工作")
        
        # 显示current的调度information
        if cron_schedule != "未设置":
            print(f"    ⏰ current调度: {cron_description}")
            
            # 提供一些常见的调度建议
            if "minute" in cron_description and "每30minute" not in cron_description and "每60minute" not in cron_description:
                print("    💡 频繁Execute模式，适合实时监控")
            elif "hour" in cron_description:
                print("    💡 按hourExecute模式，适合定期汇总")
            elif "天" in cron_description:
                print("    💡 每日Execute模式，适合日报Generate")
        
        print("    💡 如果定时任务不Execute，Check:")
        print("       • crontab 格式是否正确")
        print("       • 时区设置是否正确")
        print("       • 应用程序是否有error")
    else:
        print("    ❌ supercronic 状态abnormal")
        if pid1_cmdline:
            print(f"    📋 current PID 1: {pid1_cmdline}")
        print("    💡 建议操作:")
        print("       • 重启容器: docker restart trend-radar")
        print("       • Check容器log: docker logs trend-radar")

    # 显示logCheck建议
    print("  📋 运行状态Check:")
    print("    • 查看完整容器log: docker logs trend-radar")
    print("    • 查看实时log: docker logs -f trend-radar")
    print("    • 手动Execute测试: python manage.py run")
    print("    • 重启容器服务: docker restart trend-radar")


def show_config():
    """显示current配置"""
    print("⚙️ current配置:")

    env_vars = [
        "CRON_SCHEDULE",
        "RUN_MODE",
        "IMMEDIATE_RUN",
        "FEISHU_WEBHOOK_URL",
        "DINGTALK_WEBHOOK_URL",
        "WEWORK_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "CONFIG_PATH",
        "FREQUENCY_WORDS_PATH",
    ]

    for var in env_vars:
        value = os.environ.get(var, "未设置")
        # 隐藏敏感information
        if any(sensitive in var for sensitive in ["WEBHOOK", "TOKEN", "KEY"]):
            if value and value != "未设置":
                masked_value = value[:10] + "***" if len(value) > 10 else "***"
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: {value}")

    crontab_file = "/tmp/crontab"
    if Path(crontab_file).exists():
        print("  📅 Crontabcontent:")
        try:
            with open(crontab_file, "r") as f:
                content = f.read().strip()
                print(f"    {content}")
        except Exception as e:
            print(f"    读取failed: {e}")
    else:
        print("  📅 Crontabfiledoes not exist")


def show_files():
    """显示outputfile"""
    print("📁 outputfile:")

    output_dir = Path("/app/output")
    if not output_dir.exists():
        print("  📭 outputdirectorydoes not exist")
        return

    # 显示最近的file
    date_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)

    if not date_dirs:
        print("  📭 outputdirectory为空")
        return

    # 显示最近2天的file
    for date_dir in date_dirs[:2]:
        print(f"  📅 {date_dir.name}:")
        for subdir in ["html", "txt"]:
            sub_path = date_dir / subdir
            if sub_path.exists():
                files = list(sub_path.glob("*"))
                if files:
                    recent_files = sorted(
                        files, key=lambda x: x.stat().st_mtime, reverse=True
                    )[:3]
                    print(f"    📂 {subdir}: {len(files)} 个file")
                    for file in recent_files:
                        mtime = time.ctime(file.stat().st_mtime)
                        size_kb = file.stat().st_size // 1024
                        print(
                            f"      📄 {file.name} ({size_kb}KB, {mtime.split()[3][:5]})"
                        )
                else:
                    print(f"    📂 {subdir}: 空")


def show_logs():
    """显示实时log"""
    print("📋 实时log (按 Ctrl+C 退出):")
    print("💡 hint: 这将显示 PID 1 进程的output")
    try:
        # 尝试多种方法查看log
        log_files = [
            "/proc/1/fd/1",  # PID 1 的标准output
            "/proc/1/fd/2",  # PID 1 的标准error
        ]
        
        for log_file in log_files:
            if Path(log_file).exists():
                print(f"📄 尝试读取: {log_file}")
                subprocess.run(["tail", "-f", log_file], check=True)
                break
        else:
            print("📋 无法找到标准logfile，建议use: docker logs trend-radar")
            
    except KeyboardInterrupt:
        print("\n👋 退出log查看")
    except Exception as e:
        print(f"❌ 查看logfailed: {e}")
        print("💡 建议use: docker logs trend-radar")


def restart_supercronic():
    """重启supercronic进程"""
    print("🔄 重启supercronic...")
    print("⚠️ Note: supercronic 是 PID 1，无法直接重启")
    
    # Checkcurrent PID 1
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 current PID 1: {pid1_cmdline}")
        
        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ PID 1 是 supercronic")
            print("  💡 要重启 supercronic，need重启整个容器:")
            print("    docker restart trend-radar")
        else:
            print("  ❌ PID 1 不是 supercronic，这是abnormal状态")
            print("  💡 建议重启容器以修复问题:")
            print("    docker restart trend-radar")
    except Exception as e:
        print(f"  ❌ 无法Check PID 1: {e}")
        print("  💡 建议重启容器: docker restart trend-radar")


def show_help():
    """显示帮助information"""
    help_text = """
🐳 TrendRadar 容器管理工具

📋 命令list:
  run         - 手动Execute一次爬虫
  status      - 显示容器运行状态
  config      - 显示current配置
  files       - 显示outputfile
  logs        - 实时查看log
  restart     - 重启说明
  help        - 显示此帮助

📖 use示例:
  # 在容器中Execute
  python manage.py run
  python manage.py status
  python manage.py logs
  
  # 在宿主机Execute
  docker exec -it trend-radar python manage.py run
  docker exec -it trend-radar python manage.py status
  docker logs trend-radar

💡 常用操作指南:
  1. Check运行状态: status
     - 查看 supercronic 是否为 PID 1
     - Checkconfiguration file和关键file
     - 查看 cron 调度设置
  
  2. 手动Execute测试: run  
     - 立即Execute一次news爬取
     - 测试程序是否normal工作
  
  3. 查看log: logs
     - 实时监控运行情况
     - 也可use: docker logs trend-radar
  
  4. 重启服务: restart
     - 由于 supercronic 是 PID 1，need重启整个容器
     - use: docker restart trend-radar
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]
    commands = {
        "run": manual_run,
        "status": show_status,
        "config": show_config,
        "files": show_files,
        "logs": show_logs,
        "restart": restart_supercronic,
        "help": show_help,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n👋 操作canceled")
        except Exception as e:
            print(f"❌ Execute出错: {e}")
    else:
        print(f"❌ 未知命令: {command}")
        print("运行 'python manage.py help' 查看可用命令")


if __name__ == "__main__":
    main()