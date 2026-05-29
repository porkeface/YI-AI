"""插件系统类型定义

插件架构使用的所有数据类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class PluginType(str, Enum):
    """插件类型"""
    DIVINATION = "起卦"      # 新增起卦方式
    ANALYSIS = "分析"        # 自定义分析扩展
    INTERPRET = "解释"       # 自定义解释扩展
    RAG = "知识源"           # 自定义知识来源
    EXPORT = "导出"          # 结果导出格式


class PluginStatus(str, Enum):
    """插件状态"""
    REGISTERED = "已注册"
    ACTIVE = "已激活"
    DISABLED = "已禁用"
    ERROR = "错误"


class HookPoint(str, Enum):
    """钩子触发点

    在Agent工作流中的特定位置触发插件。
    """
    PRE_DIVINATION = "起卦前"      # 起卦前处理
    POST_DIVINATION = "起卦后"     # 起卦后处理
    PRE_ANALYSIS = "分析前"        # 规则分析前
    POST_ANALYSIS = "分析后"       # 规则分析后
    PRE_INTERPRET = "解释前"       # AI解释前
    POST_INTERPRET = "解释后"      # AI解释后
    PRE_RAG = "检索前"             # RAG检索前
    POST_RAG = "检索后"            # RAG检索后


@dataclass(frozen=True)
class PluginInfo:
    """插件元信息

    Attributes:
        plugin_id: 唯一标识
        name: 插件名称
        version: 版本号
        description: 描述
        plugin_type: 插件类型
        author: 作者
        hooks: 支持的钩子点
        enabled: 是否启用
    """
    plugin_id: str
    name: str
    version: str
    description: str
    plugin_type: PluginType
    author: str = ""
    hooks: tuple[HookPoint, ...] = ()
    enabled: bool = True


@dataclass(frozen=True)
class PluginResult:
    """插件执行结果

    Attributes:
        success: 是否成功
        data: 返回数据
        message: 消息
        modified: 是否修改了输入数据
    """
    success: bool
    data: Any = None
    message: str = ""
    modified: bool = False


@dataclass(frozen=True)
class PluginRegistration:
    """插件注册记录

    Attributes:
        info: 插件信息
        status: 当前状态
        hook_handlers: 钩子处理器映射
    """
    info: PluginInfo
    status: PluginStatus = PluginStatus.REGISTERED
    hook_handlers: tuple[tuple[HookPoint, str], ...] = ()


# ---- Plugin Protocols ----


@runtime_checkable
class DivinationPluginProtocol(Protocol):
    """起卦插件协议

    实现此协议可新增起卦方式。
    """

    @staticmethod
    def get_plugin_info() -> PluginInfo:
        """返回插件元信息"""
        ...

    @staticmethod
    def divinate(params: dict[str, Any]) -> PluginResult:
        """执行起卦

        Args:
            params: 起卦参数

        Returns:
            包含卦象数据的插件结果
        """
        ...


@runtime_checkable
class AnalysisPluginProtocol(Protocol):
    """分析插件协议

    实现此协议可扩展规则分析。
    """

    @staticmethod
    def get_plugin_info() -> PluginInfo:
        """返回插件元信息"""
        ...

    @staticmethod
    def analyze(
        hexagram_data: dict[str, Any],
        context: dict[str, Any],
    ) -> PluginResult:
        """执行自定义分析

        Args:
            hexagram_data: 卦象数据
            context: 上下文信息

        Returns:
            分析结果
        """
        ...


@runtime_checkable
class InterpretPluginProtocol(Protocol):
    """解释插件协议

    实现此协议可扩展AI解释。
    """

    @staticmethod
    def get_plugin_info() -> PluginInfo:
        """返回插件元信息"""
        ...

    @staticmethod
    def enhance_prompt(
        base_prompt: str,
        context: dict[str, Any],
    ) -> PluginResult:
        """增强Prompt

        Args:
            base_prompt: 基础Prompt
            context: 上下文信息

        Returns:
            增强后的Prompt
        """
        ...

    @staticmethod
    def post_process(
        interpretation: str,
        context: dict[str, Any],
    ) -> PluginResult:
        """后处理解释结果

        Args:
            interpretation: AI解释文本
            context: 上下文信息

        Returns:
            处理后的解释文本
        """
        ...


@runtime_checkable
class RAGPluginProtocol(Protocol):
    """知识源插件协议

    实现此协议可扩展RAG知识来源。
    """

    @staticmethod
    def get_plugin_info() -> PluginInfo:
        """返回插件元信息"""
        ...

    @staticmethod
    def retrieve(
        query: str,
        top_k: int = 5,
    ) -> PluginResult:
        """检索相关知识

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索到的知识列表
        """
        ...
