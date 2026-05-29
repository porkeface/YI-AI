"""插件系统测试

覆盖：插件注册表、插件管理器、类型定义。
"""

from __future__ import annotations

import pytest
from ai.plugins.types import (
    PluginType,
    PluginStatus,
    HookPoint,
    PluginInfo,
    PluginResult,
    PluginRegistration,
)
from ai.plugins.registry import PluginRegistry
from ai.plugins.manager import PluginManager


def _make_plugin_info(
    plugin_id: str = "test_plugin",
    name: str = "测试插件",
    plugin_type: PluginType = PluginType.DIVINATION,
    hooks: tuple[HookPoint, ...] = (),
    enabled: bool = True,
) -> PluginInfo:
    """创建测试用插件信息"""
    return PluginInfo(
        plugin_id=plugin_id,
        name=name,
        version="1.0.0",
        description="测试插件",
        plugin_type=plugin_type,
        author="测试",
        hooks=hooks,
        enabled=enabled,
    )


# ============================================================
# 插件注册表测试
# ============================================================


class TestPluginRegistry:
    """插件注册表测试"""

    def setup_method(self):
        """每个测试前清空注册表"""
        PluginRegistry.clear()

    def test_register_plugin(self):
        """注册插件"""
        info = _make_plugin_info()
        result = PluginRegistry.register(info)
        assert result is True
        assert PluginRegistry.count() == 1

    def test_register_duplicate(self):
        """重复注册失败"""
        info = _make_plugin_info()
        PluginRegistry.register(info)
        result = PluginRegistry.register(info)
        assert result is False

    def test_unregister_plugin(self):
        """注销插件"""
        info = _make_plugin_info()
        PluginRegistry.register(info)
        result = PluginRegistry.unregister("test_plugin")
        assert result is True
        assert PluginRegistry.count() == 0

    def test_unregister_nonexistent(self):
        """注销不存在的插件"""
        result = PluginRegistry.unregister("nonexistent")
        assert result is False

    def test_enable_disable(self):
        """启用/禁用插件"""
        info = _make_plugin_info(enabled=False)
        PluginRegistry.register(info)

        reg = PluginRegistry.get_plugin("test_plugin")
        assert reg.status == PluginStatus.DISABLED

        PluginRegistry.enable("test_plugin")
        reg = PluginRegistry.get_plugin("test_plugin")
        assert reg.status == PluginStatus.ACTIVE

        PluginRegistry.disable("test_plugin")
        reg = PluginRegistry.get_plugin("test_plugin")
        assert reg.status == PluginStatus.DISABLED

    def test_list_plugins(self):
        """列出插件"""
        PluginRegistry.register(
            _make_plugin_info("p1", "插件1", PluginType.DIVINATION)
        )
        PluginRegistry.register(
            _make_plugin_info("p2", "插件2", PluginType.ANALYSIS)
        )

        all_plugins = PluginRegistry.list_plugins()
        assert len(all_plugins) == 2

        divination_plugins = PluginRegistry.list_plugins(
            plugin_type=PluginType.DIVINATION
        )
        assert len(divination_plugins) == 1

    def test_hook_handlers(self):
        """钩子处理器注册"""
        info = _make_plugin_info(
            hooks=(HookPoint.POST_DIVINATION, HookPoint.PRE_ANALYSIS)
        )
        handlers = {
            HookPoint.POST_DIVINATION: "module:handler1",
            HookPoint.PRE_ANALYSIS: "module:handler2",
        }
        PluginRegistry.register(info, handlers)

        post_handlers = PluginRegistry.get_hook_handlers(
            HookPoint.POST_DIVINATION
        )
        assert len(post_handlers) == 1
        assert post_handlers[0] == ("test_plugin", "module:handler1")

    def test_hook_handlers_disabled_plugin(self):
        """禁用插件的钩子不返回"""
        info = _make_plugin_info(
            enabled=False,
            hooks=(HookPoint.POST_DIVINATION,),
        )
        handlers = {HookPoint.POST_DIVINATION: "module:handler1"}
        PluginRegistry.register(info, handlers)

        post_handlers = PluginRegistry.get_hook_handlers(
            HookPoint.POST_DIVINATION
        )
        assert len(post_handlers) == 0

    def test_clear(self):
        """清空注册表"""
        PluginRegistry.register(_make_plugin_info("p1"))
        PluginRegistry.register(_make_plugin_info("p2"))
        assert PluginRegistry.count() == 2

        PluginRegistry.clear()
        assert PluginRegistry.count() == 0

    def test_count(self):
        """计数"""
        assert PluginRegistry.count() == 0
        PluginRegistry.register(_make_plugin_info("p1"))
        assert PluginRegistry.count() == 1
        PluginRegistry.register(_make_plugin_info("p2"))
        assert PluginRegistry.count() == 2


# ============================================================
# 插件管理器测试
# ============================================================


class TestPluginManager:
    """插件管理器测试"""

    def setup_method(self):
        """每个测试前清空注册表"""
        PluginRegistry.clear()

    def test_invoke_hook_no_plugins(self):
        """无插件时调用钩子"""
        results = PluginManager.invoke_hook(
            HookPoint.POST_DIVINATION, {}
        )
        assert results == ()

    def test_get_plugin_summary(self):
        """获取插件摘要"""
        PluginRegistry.register(
            _make_plugin_info("p1", "插件1", PluginType.DIVINATION)
        )
        PluginRegistry.register(
            _make_plugin_info("p2", "插件2", PluginType.ANALYSIS)
        )

        summary = PluginManager.get_plugin_summary()
        assert summary["total"] == 2
        assert summary["active"] == 2
        assert summary["by_type"]["起卦"] == 1
        assert summary["by_type"]["分析"] == 1

    def test_discover_plugins_nonexistent(self):
        """发现不存在的包"""
        count = PluginManager.discover_plugins(
            "/nonexistent/path", "nonexistent.package"
        )
        assert count == 0


# ============================================================
# 类型测试
# ============================================================


class TestPluginTypes:
    """插件类型测试"""

    def test_plugin_info_frozen(self):
        """PluginInfo 不可变"""
        info = _make_plugin_info()
        with pytest.raises(AttributeError):
            info.name = "新名称"  # type: ignore

    def test_plugin_result_frozen(self):
        """PluginResult 不可变"""
        result = PluginResult(success=True, data="test")
        with pytest.raises(AttributeError):
            result.success = False  # type: ignore

    def test_plugin_registration_frozen(self):
        """PluginRegistration 不可变"""
        info = _make_plugin_info()
        reg = PluginRegistration(info=info)
        with pytest.raises(AttributeError):
            reg.status = PluginStatus.ACTIVE  # type: ignore

    def test_plugin_type_enum(self):
        """插件类型枚举值"""
        assert PluginType.DIVINATION.value == "起卦"
        assert PluginType.ANALYSIS.value == "分析"
        assert PluginType.INTERPRET.value == "解释"
        assert PluginType.RAG.value == "知识源"
        assert PluginType.EXPORT.value == "导出"

    def test_hook_point_enum(self):
        """钩子点枚举值"""
        assert HookPoint.PRE_DIVINATION.value == "起卦前"
        assert HookPoint.POST_DIVINATION.value == "起卦后"
        assert HookPoint.PRE_ANALYSIS.value == "分析前"
        assert HookPoint.POST_ANALYSIS.value == "分析后"

    def test_plugin_status_enum(self):
        """插件状态枚举值"""
        assert PluginStatus.REGISTERED.value == "已注册"
        assert PluginStatus.ACTIVE.value == "已激活"
        assert PluginStatus.DISABLED.value == "已禁用"
        assert PluginStatus.ERROR.value == "错误"
