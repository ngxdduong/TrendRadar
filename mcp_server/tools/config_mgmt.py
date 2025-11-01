"""
Configuration Management工具

实现配置query和管理功能。
"""

from typing import Dict, Optional

from ..services.data_service import DataService
from ..utils.validators import validate_config_section
from ..utils.errors import MCPError


class ConfigManagementTools:
    """Configuration Management工具类"""

    def __init__(self, project_root: str = None):
        """
        InitializeConfiguration Management工具

        Args:
            project_root: 项目根directory
        """
        self.data_service = DataService(project_root)

    def get_current_config(self, section: Optional[str] = None) -> Dict:
        """
        Getcurrent系统配置

        Args:
            section: 配置节 - all/crawler/push/keywords/weights，defaultall

        Returns:
            配置dictionary

        Example:
            >>> tools = ConfigManagementTools()
            >>> result = tools.get_current_config(section="crawler")
            >>> print(result['crawler']['platforms'])
        """
        try:
            # 参数Validate
            section = validate_config_section(section)

            # Get配置
            config = self.data_service.get_current_config(section=section)

            return {
                "config": config,
                "section": section,
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
