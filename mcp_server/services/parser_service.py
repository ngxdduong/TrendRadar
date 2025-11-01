"""
fileParse服务

提供txt格式newsdata和YAMLconfiguration file的Parse功能。
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import yaml

from ..utils.errors import FileParseError, DataNotFoundError
from .cache_service import get_cache


class ParserService:
    """fileParse服务类"""

    def __init__(self, project_root: str = None):
        """
        InitializeParse服务

        Args:
            project_root: 项目根directory，default为currentdirectory的父directory
        """
        if project_root is None:
            # Getcurrentfile所在directory的父directory的父directory
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        # Initialize缓存服务
        self.cache = get_cache()

    @staticmethod
    def clean_title(title: str) -> str:
        """
        清理title文本

        Args:
            title: 原始title

        Returns:
            清理后的title
        """
        # 移除多余空白
        title = re.sub(r'\s+', ' ', title)
        # 移除特殊字符
        title = title.strip()
        return title

    def parse_txt_file(self, file_path: Path) -> Tuple[Dict, Dict]:
        """
        Parse单个txtfile的titledata

        Args:
            file_path: txtfilepath

        Returns:
            (titles_by_id, id_to_name) 元组
            - titles_by_id: {platform_id: {title: {ranks, url, mobileUrl}}}
            - id_to_name: {platform_id: platform_name}

        Raises:
            FileParseError: File parse error
        """
        if not file_path.exists():
            raise FileParseError(str(file_path), "filedoes not exist")

        titles_by_id = {}
        id_to_name = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                sections = content.split("\n\n")

                for section in sections:
                    if not section.strip() or "==== 以下ID请求failed ====" in section:
                        continue

                    lines = section.strip().split("\n")
                    if len(lines) < 2:
                        continue

                    # Parseheader: id | name 或 id
                    header_line = lines[0].strip()
                    if " | " in header_line:
                        parts = header_line.split(" | ", 1)
                        source_id = parts[0].strip()
                        name = parts[1].strip()
                        id_to_name[source_id] = name
                    else:
                        source_id = header_line
                        id_to_name[source_id] = source_id

                    titles_by_id[source_id] = {}

                    # Parsetitle行
                    for line in lines[1:]:
                        if line.strip():
                            try:
                                title_part = line.strip()
                                rank = None

                                # 提取rank
                                if ". " in title_part and title_part.split(". ")[0].isdigit():
                                    rank_str, title_part = title_part.split(". ", 1)
                                    rank = int(rank_str)

                                # 提取 MOBILE URL
                                mobile_url = ""
                                if " [MOBILE:" in title_part:
                                    title_part, mobile_part = title_part.rsplit(" [MOBILE:", 1)
                                    if mobile_part.endswith("]"):
                                        mobile_url = mobile_part[:-1]

                                # 提取 URL
                                url = ""
                                if " [URL:" in title_part:
                                    title_part, url_part = title_part.rsplit(" [URL:", 1)
                                    if url_part.endswith("]"):
                                        url = url_part[:-1]

                                title = self.clean_title(title_part.strip())
                                ranks = [rank] if rank is not None else [1]

                                titles_by_id[source_id][title] = {
                                    "ranks": ranks,
                                    "url": url,
                                    "mobileUrl": mobile_url,
                                }

                            except Exception as e:
                                # 忽略单行Parseerror
                                continue

        except Exception as e:
            raise FileParseError(str(file_path), str(e))

        return titles_by_id, id_to_name

    def get_date_folder_name(self, date: datetime = None) -> str:
        """
        Getdatefile夹名称

        Args:
            date: date对象，default为today

        Returns:
            file夹名称，格式: YYYY年MM月DD日
        """
        if date is None:
            date = datetime.now()
        return date.strftime("%Y年%m月%d日")

    def read_all_titles_for_date(
        self,
        date: datetime = None,
        platform_ids: Optional[List[str]] = None
    ) -> Tuple[Dict, Dict, Dict]:
        """
        读取指定date的所有titlefile（带缓存）

        Args:
            date: date对象，default为today
            platform_ids: List of platform IDs，None表示所有Platform

        Returns:
            (all_titles, id_to_name, all_timestamps) 元组
            - all_titles: {platform_id: {title: {ranks, url, mobileUrl, ...}}}
            - id_to_name: {platform_id: platform_name}
            - all_timestamps: {filename: timestamp}

        Raises:
            DataNotFoundError: datadoes not exist
        """
        # Generate缓存键
        date_str = self.get_date_folder_name(date)
        platform_key = ','.join(sorted(platform_ids)) if platform_ids else 'all'
        cache_key = f"read_all_titles:{date_str}:{platform_key}"

        # 尝试从缓存Get
        # 对于historydata（非today），use更长的缓存time（1hour）
        # 对于today的data，use较短的缓存time（15minute），因为可能有新data
        is_today = (date is None) or (date.date() == datetime.now().date())
        ttl = 900 if is_today else 3600  # 15minute vs 1hour

        cached = self.cache.get(cache_key, ttl=ttl)
        if cached:
            return cached

        # 缓存未命中，读取file
        date_folder = self.get_date_folder_name(date)
        txt_dir = self.project_root / "output" / date_folder / "txt"

        if not txt_dir.exists():
            raise DataNotFoundError(
                f"未找到 {date_folder} 的datadirectory",
                suggestion="请先运行爬虫或Checkdate是否正确"
            )

        all_titles = {}
        id_to_name = {}
        all_timestamps = {}

        # 读取所有txtfile
        txt_files = sorted(txt_dir.glob("*.txt"))

        if not txt_files:
            raise DataNotFoundError(
                f"{date_folder} 没有datafile",
                suggestion="Please wait爬虫任务完成"
            )

        for txt_file in txt_files:
            try:
                titles_by_id, file_id_to_name = self.parse_txt_file(txt_file)

                # Updateid_to_name
                id_to_name.update(file_id_to_name)

                # 合并titledata
                for platform_id, titles in titles_by_id.items():
                    # 如果指定了Platform过滤
                    if platform_ids and platform_id not in platform_ids:
                        continue

                    if platform_id not in all_titles:
                        all_titles[platform_id] = {}

                    for title, info in titles.items():
                        if title in all_titles[platform_id]:
                            # 合并rank
                            all_titles[platform_id][title]["ranks"].extend(info["ranks"])
                        else:
                            all_titles[platform_id][title] = info.copy()

                # recordfiletime戳
                all_timestamps[txt_file.name] = txt_file.stat().st_mtime

            except Exception as e:
                # 忽略单个file的Parseerror，继续Process其他file
                print(f"Warning: Failed to parse file {txt_file} failed: {e}")
                continue

        if not all_titles:
            raise DataNotFoundError(
                f"{date_folder} 没有有效的data",
                suggestion="请Checkdatafile格式或重新运行爬虫"
            )

        # 缓存result
        result = (all_titles, id_to_name, all_timestamps)
        self.cache.set(cache_key, result)

        return result

    def parse_yaml_config(self, config_path: str = None) -> dict:
        """
        ParseYAMLconfiguration file

        Args:
            config_path: configuration filepath，default为 config/config.yaml

        Returns:
            配置dictionary

        Raises:
            FileParseError: 配置File parse error
        """
        if config_path is None:
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileParseError(str(config_path), "configuration filedoes not exist")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return config_data
        except Exception as e:
            raise FileParseError(str(config_path), str(e))

    def parse_frequency_words(self, words_file: str = None) -> List[Dict]:
        """
        Parse关键词configuration file

        Args:
            words_file: 关键词filepath，default为 config/frequency_words.txt

        Returns:
            词组list

        Raises:
            FileParseError: File parse error
        """
        if words_file is None:
            words_file = self.project_root / "config" / "frequency_words.txt"
        else:
            words_file = Path(words_file)

        if not words_file.exists():
            return []

        word_groups = []

        try:
            with open(words_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # use | 分隔符
                    parts = [p.strip() for p in line.split("|")]
                    if not parts:
                        continue

                    group = {
                        "required": [],
                        "normal": [],
                        "filter_words": []
                    }

                    for part in parts:
                        if not part:
                            continue

                        words = [w.strip() for w in part.split(",")]
                        for word in words:
                            if not word:
                                continue
                            if word.endswith("+"):
                                # 必须词
                                group["required"].append(word[:-1])
                            elif word.endswith("!"):
                                # 过滤词
                                group["filter_words"].append(word[:-1])
                            else:
                                # 普通词
                                group["normal"].append(word)

                    if group["required"] or group["normal"]:
                        word_groups.append(group)

        except Exception as e:
            raise FileParseError(str(words_file), str(e))

        return word_groups
