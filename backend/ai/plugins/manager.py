"""插件管理器

提供插件执行、钩子调用、插件发现的高级接口。
与 PluginRegistry 配合，管理插件生命周期。
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Any, Sequence

from ai.plugins.registry import PluginRegistry
from ai.plugins.types import (
    HookPoint,
    PluginInfo,
    PluginResult,
    PluginType,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器

    classmethod-only API — 提供插件执行和发现的高级功能。
    """

    @classmethod
    def invoke_hook(
        cls,
        hook: HookPoint,
        context: dict[str, Any],
        plugin_type: type | None = None,
    ) -> tuple[PluginResult, ...]:
        """调用钩子点的所有注册处理器

        按注册顺序依次调用，每个插件的结果累积返回。

        Args:
            hook: 钩子点
            context: 传递给处理器的上下文数据
            plugin_type: 插件协议类型（用于查找方法）

        Returns:
            所有处理器的结果列表
        """
        handlers = PluginRegistry.get_hook_handlers(hook)
        results: list[PluginResult] = []

        for plugin_id, handler_name in handlers:
            try:
                result = cls._execute_handler(
                    plugin_id, handler_name, context
                )
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(
                    "plugin_hook_error: %s hook=%s error=%s",
                    plugin_id, hook.value, str(e),
                )
                results.append(
                    PluginResult(
                        success=False,
                        message=f"插件{plugin_id}执行失败: {e}",
                    )
                )

        return tuple(results)

    @classmethod
    def _execute_handler(
        cls,
        plugin_id: str,
        handler_name: str,
        context: dict[str, Any],
    ) -> PluginResult | None:
        """执行单个处理器

        Args:
            plugin_id: 插件ID
            handler_name: 处理器函数/方法名
            context: 上下文数据

        Returns:
            处理结果
        """
        # 从注册信息中获取插件模块
        reg = PluginRegistry.get_plugin(plugin_id)
        if reg is None:
            return None

        # handler_name 格式: "module.path:function_name"
        if ":" in handler_name:
            module_path, func_name = handler_name.rsplit(":", 1)
            try:
                module = importlib.import_module(module_path)
                handler = getattr(module, func_name, None)
                if handler is None:
                    logger.error(
                        "handler_not_found: %s:%s",
                        module_path, func_name,
                    )
                    return None
                return handler(context)
            except ImportError as e:
                logger.error(
                    "module_import_error: %s error=%s",
                    module_path, str(e),
                )
                return None

        return None

    @classmethod
    def discover_plugins(
        cls,
        package_path: str,
        package_name: str,
    ) -> int:
        """自动发现并注册插件

        扫描指定包下的所有模块，查找实现插件协议的类。

        Args:
            package_path: 包的文件系统路径
            package_name: 包的Python模块名

        Returns:
            发现并注册的插件数量
        """
        count = 0

        try:
            package = importlib.import_module(package_name)
        except (ImportError, ModuleNotFoundError) as e:
            logger.error(
                "plugin_package_import_error: %s error=%s",
                package_name, str(e),
            )
            return 0

        for importer, modname, ispkg in pkgutil.iter_modules(
            package.__path__, prefix=package_name + "."
        ):
            try:
                module = importlib.import_module(modname)
                # 查找模块中的 PluginInfo 和注册函数
                register_func = getattr(module, "register_plugin", None)
                if register_func and callable(register_func):
                    info = register_func()
                    if isinstance(info, PluginInfo):
                        PluginRegistry.register(info)
                        count += 1
                        logger.info(
                            "plugin_discovered: %s (%s)",
                            modname, info.plugin_id,
                        )
            except Exception as e:
                logger.warning(
                    "plugin_discovery_error: %s error=%s",
                    modname, str(e),
                )

        return count

    @classmethod
    def get_plugin_summary(cls) -> dict[str, Any]:
        """获取插件系统摘要

        Returns:
            包含插件统计的字典
        """
        from ai.plugins.types import PluginStatus

        all_plugins = PluginRegistry.list_plugins()
        active_plugins = PluginRegistry.list_plugins(
            status=PluginStatus.ACTIVE,
        )

        type_counts: dict[str, int] = {}
        for p in all_plugins:
            type_name = p.plugin_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total": len(all_plugins),
            "active": len(active_plugins),
            "by_type": type_counts,
        }
