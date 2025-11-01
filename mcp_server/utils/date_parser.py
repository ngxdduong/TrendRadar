"""
Date Parsing Tool

Supports parsing of multiple natural language date formats, including relative and absolute dates。
"""

import re
from datetime import datetime, timedelta

from .errors import InvalidParameterError


class DateParser:
    """Date parser class"""

    # 中文date映射
    CN_DATE_MAPPING = {
        "today": 0,
        "yesterday": 1,
        "the day before yesterday": 2,
        "three days ago": 3,
    }

    # 英文date映射
    EN_DATE_MAPPING = {
        "today": 0,
        "yesterday": 1,
    }

    # 星期映射
    WEEKDAY_CN = {
        "一": 0, "二": 1, "三": 2, "四": 3,
        "五": 4, "六": 5, "日": 6, "天": 6
    }

    WEEKDAY_EN = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    @staticmethod
    def parse_date_query(date_query: str) -> datetime:
        """
        Parse date query string

        support的格式：
        - 相对date（中文）：today、yesterday、the day before yesterday、three days ago、N天前
        - 相对date（英文）：today、yesterday、N days ago
        - 星期（中文）：上周一、上周二、本周三
        - 星期（英文）：last monday、this friday
        - 绝对date：2025-10-10、10月10日、2025年10月10日

        Args:
            date_query: Date query string

        Returns:
            datetime object

        Raises:
            InvalidParameterError: date格式无法识别

        Examples:
            >>> DateParser.parse_date_query("today")
            datetime(2025, 10, 11)
            >>> DateParser.parse_date_query("yesterday")
            datetime(2025, 10, 10)
            >>> DateParser.parse_date_query("3天前")
            datetime(2025, 10, 8)
            >>> DateParser.parse_date_query("2025-10-10")
            datetime(2025, 10, 10)
        """
        if not date_query or not isinstance(date_query, str):
            raise InvalidParameterError(
                "Date query string cannot be empty",
                suggestion="Please provide有效的datequery，如：today、yesterday、2025-10-10"
            )

        date_query = date_query.strip().lower()

        # 1. 尝试Parse中文常用相对date
        if date_query in DateParser.CN_DATE_MAPPING:
            days_ago = DateParser.CN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 2. 尝试Parse英文常用相对date
        if date_query in DateParser.EN_DATE_MAPPING:
            days_ago = DateParser.EN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 3. 尝试Parse "N天前" 或 "N days ago"
        cn_days_ago_match = re.match(r'(\d+)\s*天前', date_query)
        if cn_days_ago_match:
            days = int(cn_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"天数过大: {days}天",
                    suggestion="请useless than365天的相对date或use绝对date"
                )
            return datetime.now() - timedelta(days=days)

        en_days_ago_match = re.match(r'(\d+)\s*days?\s+ago', date_query)
        if en_days_ago_match:
            days = int(en_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"天数过大: {days}天",
                    suggestion="请useless than365天的相对date或use绝对date"
                )
            return datetime.now() - timedelta(days=days)

        # 4. 尝试Parse星期（中文）：上周一、本周三
        cn_weekday_match = re.match(r'(上|本)周([一二三四五六日天])', date_query)
        if cn_weekday_match:
            week_type = cn_weekday_match.group(1)  # 上 或 本
            weekday_str = cn_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_CN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "上")

        # 5. 尝试Parse星期（英文）：last monday、this friday
        en_weekday_match = re.match(r'(last|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_query)
        if en_weekday_match:
            week_type = en_weekday_match.group(1)  # last 或 this
            weekday_str = en_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_EN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "last")

        # 6. 尝试Parse绝对date：YYYY-MM-DD
        iso_date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_query)
        if iso_date_match:
            year = int(iso_date_match.group(1))
            month = int(iso_date_match.group(2))
            day = int(iso_date_match.group(3))
            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"无效的date: {date_query}",
                    suggestion=f"date值error: {str(e)}"
                )

        # 7. 尝试Parse中文date：MM月DD日 或 YYYY年MM月DD日
        cn_date_match = re.match(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日', date_query)
        if cn_date_match:
            year_str = cn_date_match.group(1)
            month = int(cn_date_match.group(2))
            day = int(cn_date_match.group(3))

            # 如果没有年份，usecurrent年份
            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                # 如果月份greater thancurrent月份，说明是去年
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"无效的date: {date_query}",
                    suggestion=f"date值error: {str(e)}"
                )

        # 8. 尝试Parse斜杠格式：YYYY/MM/DD 或 MM/DD
        slash_date_match = re.match(r'(?:(\d{4})/)?(\d{1,2})/(\d{1,2})', date_query)
        if slash_date_match:
            year_str = slash_date_match.group(1)
            month = int(slash_date_match.group(2))
            day = int(slash_date_match.group(3))

            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"无效的date: {date_query}",
                    suggestion=f"date值error: {str(e)}"
                )

        # 如果所有格式都不匹配
        raise InvalidParameterError(
            f"无法识别的date格式: {date_query}",
            suggestion=(
                "support的格式:\n"
                "- 相对date: today、yesterday、the day before yesterday、3天前、today、yesterday、3 days ago\n"
                "- 星期: 上周一、本周三、last monday、this friday\n"
                "- 绝对date: 2025-10-10、10月10日、2025年10月10日"
            )
        )

    @staticmethod
    def _get_date_by_weekday(target_weekday: int, is_last_week: bool) -> datetime:
        """
        根据星期几Getdate

        Args:
            target_weekday: 目标星期 (0=周一, 6=周日)
            is_last_week: 是否是上周

        Returns:
            datetime object
        """
        today = datetime.now()
        current_weekday = today.weekday()

        # 计算天数差
        if is_last_week:
            # 上周的某一天
            days_diff = current_weekday - target_weekday + 7
        else:
            # 本周的某一天
            days_diff = current_weekday - target_weekday
            if days_diff < 0:
                days_diff += 7

        return today - timedelta(days=days_diff)

    @staticmethod
    def format_date_folder(date: datetime) -> str:
        """
        将date格式化为file夹名称

        Args:
            date: datetime object

        Returns:
            file夹名称，格式: YYYY年MM月DD日

        Examples:
            >>> DateParser.format_date_folder(datetime(2025, 10, 11))
            '2025年10月11日'
        """
        return date.strftime("%Y年%m月%d日")

    @staticmethod
    def validate_date_not_future(date: datetime) -> None:
        """
        Validate date is not in the future

        Args:
            date: 待Validate的date

        Raises:
            InvalidParameterError: date在未来
        """
        if date.date() > datetime.now().date():
            raise InvalidParameterError(
                f"不能query未来的date: {date.strftime('%Y-%m-%d')}",
                suggestion="请usetoday或过去的date"
            )

    @staticmethod
    def validate_date_not_too_old(date: datetime, max_days: int = 365) -> None:
        """
        Validate date is not too old

        Args:
            date: 待Validate的date
            max_days: 最大天数

        Raises:
            InvalidParameterError: date太久远
        """
        days_ago = (datetime.now().date() - date.date()).days
        if days_ago > max_days:
            raise InvalidParameterError(
                f"date太久远: {date.strftime('%Y-%m-%d')} ({days_ago}天前)",
                suggestion=f"请query{max_days}天内的data"
            )
