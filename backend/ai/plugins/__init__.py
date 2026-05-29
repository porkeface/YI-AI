"""插件系统模块

可扩展插件架构，支持第三方开发插件扩展占卜体系。

核心组件：
- PluginRegistry: 插件注册表（注册、激活、禁用、查询）
- PluginManager: 插件管理器（执行、钩子调用、自动发现）
- 类型定义: 插件协议、钩子点、插件类型
"""

from ai.plugins.registry import PluginRegistry
from ai.plugins.manager import PluginManager
from ai.plugins.types import (
    PluginType,
    PluginStatus,
    HookPoint,
    PluginInfo,
    PluginResult,
    PluginRegistration,
    DivinationPluginProtocol,
    AnalysisPluginProtocol,
    InterpretPluginProtocol,
    RAGPluginProtocol,
)

__all__ = [
    # 核心
    "PluginRegistry",
    "PluginManager",
    # 类型
    "PluginType",
    "PluginStatus",
    "HookPoint",
    "PluginInfo",
    "PluginResult",
    "PluginRegistration",
    # 协议
    "DivinationPluginProtocol",
    "AnalysisPluginProtocol",
    "InterpretPluginProtocol",
    "RAGPluginProtocol",
]
