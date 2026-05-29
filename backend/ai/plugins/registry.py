"""插件注册表

集中管理所有插件的注册、激活、禁用和查询。
线程安全 — 使用 threading.Lock 保护共享状态。
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Sequence

from ai.plugins.types import (
    HookPoint,
    PluginInfo,
    PluginRegistration,
    PluginResult,
    PluginStatus,
    PluginType,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """插件注册表

    classmethod-only API — 所有状态存储在模块级变量中。
    线程安全 — 使用锁保护共享状态。
    """

    # 模块级状态
    _plugins: dict[str, PluginRegistration] = {}
    _hook_map: dict[HookPoint, list[str]] = {}
    _lock = threading.Lock()

    @classmethod
    def register(
        cls,
        info: PluginInfo,
        hook_handlers: dict[HookPoint, Any] | None = None,
    ) -> bool:
        """注册插件

        Args:
            info: 插件信息
            hook_handlers: 钩子处理器映射 {钩子点: 处理器函数名}

        Returns:
            是否注册成功
        """
        with cls._lock:
            if info.plugin_id in cls._plugins:
                logger.warning(
                    "plugin_already_registered: %s", info.plugin_id
                )
                return False

            # 构建注册记录
            handlers_tuple = tuple(
                (hook, handler_name)
                for hook, handler_name in (hook_handlers or {}).items()
            )
            registration = PluginRegistration(
                info=info,
                status=(
                    PluginStatus.ACTIVE if info.enabled
                    else PluginStatus.DISABLED
                ),
                hook_handlers=handlers_tuple,
            )

            cls._plugins[info.plugin_id] = registration

            # 更新钩子映射
            for hook, _ in handlers_tuple:
                cls._hook_map.setdefault(hook, []).append(info.plugin_id)

            logger.info(
                "plugin_registered: %s (%s, %s)",
                info.plugin_id, info.name, info.plugin_type.value,
            )
            return True

    @classmethod
    def unregister(cls, plugin_id: str) -> bool:
        """注销插件

        Args:
            plugin_id: 插件ID

        Returns:
            是否注销成功
        """
        with cls._lock:
            if plugin_id not in cls._plugins:
                return False

            registration = cls._plugins[plugin_id]

            # 清理钩子映射
            for hook, _ in registration.hook_handlers:
                if hook in cls._hook_map:
                    cls._hook_map[hook] = [
                        pid for pid in cls._hook_map[hook]
                        if pid != plugin_id
                    ]

            del cls._plugins[plugin_id]

            logger.info("plugin_unregistered", plugin_id=plugin_id)
            return True

    @classmethod
    def enable(cls, plugin_id: str) -> bool:
        """启用插件

        Args:
            plugin_id: 插件ID

        Returns:
            是否操作成功
        """
        with cls._lock:
            if plugin_id not in cls._plugins:
                return False

            reg = cls._plugins[plugin_id]
            cls._plugins[plugin_id] = PluginRegistration(
                info=reg.info,
                status=PluginStatus.ACTIVE,
                hook_handlers=reg.hook_handlers,
            )
            return True

    @classmethod
    def disable(cls, plugin_id: str) -> bool:
        """禁用插件

        Args:
            plugin_id: 插件ID

        Returns:
            是否操作成功
        """
        with cls._lock:
            if plugin_id not in cls._plugins:
                return False

            reg = cls._plugins[plugin_id]
            cls._plugins[plugin_id] = PluginRegistration(
                info=reg.info,
                status=PluginStatus.DISABLED,
                hook_handlers=reg.hook_handlers,
            )
            return True

    @classmethod
    def get_plugin(cls, plugin_id: str) -> PluginRegistration | None:
        """获取插件注册信息

        Args:
            plugin_id: 插件ID

        Returns:
            插件注册记录，不存在返回 None
        """
        with cls._lock:
            return cls._plugins.get(plugin_id)

    @classmethod
    def list_plugins(
        cls,
        plugin_type: PluginType | None = None,
        status: PluginStatus | None = None,
    ) -> tuple[PluginInfo, ...]:
        """列出插件

        Args:
            plugin_type: 按类型筛选
            status: 按状态筛选

        Returns:
            符合条件的插件信息列表
        """
        with cls._lock:
            results = []
            for reg in cls._plugins.values():
                if plugin_type and reg.info.plugin_type != plugin_type:
                    continue
                if status and reg.status != status:
                    continue
                results.append(reg.info)
            return tuple(results)

    @classmethod
    def get_hook_handlers(
        cls,
        hook: HookPoint,
    ) -> tuple[tuple[str, Any], ...]:
        """获取指定钩子点的所有处理器

        Args:
            hook: 钩子点

        Returns:
            (插件ID, 处理器函数名) 元组列表
        """
        with cls._lock:
            plugin_ids = cls._hook_map.get(hook, [])
            results = []
            for pid in plugin_ids:
                reg = cls._plugins.get(pid)
                if reg and reg.status == PluginStatus.ACTIVE:
                    for h, handler_name in reg.hook_handlers:
                        if h == hook:
                            results.append((pid, handler_name))
            return tuple(results)

    @classmethod
    def clear(cls) -> None:
        """清空所有插件（用于测试）"""
        with cls._lock:
            cls._plugins.clear()
            cls._hook_map.clear()

    @classmethod
    def count(cls) -> int:
        """获取已注册插件数量"""
        with cls._lock:
            return len(cls._plugins)
