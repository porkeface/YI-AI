"""插件管理API

连接 ai.plugins.registry.PluginRegistry 和 ai.plugins.manager.PluginManager，
提供插件注册、启用/禁用、查询接口。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai.plugins.manager import PluginManager
from ai.plugins.registry import PluginRegistry
from ai.plugins.types import HookPoint, PluginInfo, PluginType

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

# 插件类型字符串 -> 枚举映射
_TYPE_MAP = {
    "divination": PluginType.DIVINATION,
    "analysis": PluginType.ANALYSIS,
    "interpret": PluginType.INTERPRET,
    "rag": PluginType.RAG,
    "export": PluginType.EXPORT,
}


class PluginRegisterRequest(BaseModel):
    """插件注册请求"""
    plugin_id: str = Field(..., description="插件唯一标识")
    name: str = Field(..., description="插件名称")
    version: str = Field("1.0.0", description="版本号")
    description: str = Field("", description="插件描述")
    plugin_type: str = Field(..., description="插件类型: divination / analysis / interpret / rag / export")
    author: str = Field("", description="作者")
    enabled: bool = Field(True, description="是否启用")


class PluginToggleRequest(BaseModel):
    """插件启用/禁用请求"""
    enabled: bool


@router.get("/list")
async def list_plugins(plugin_type: str | None = None):
    """列出所有插件"""
    ptype = None
    if plugin_type:
        ptype = _TYPE_MAP.get(plugin_type)
        if ptype is None:
            raise HTTPException(
                status_code=400,
                detail=f"无效的插件类型: {plugin_type}，可选值: {list(_TYPE_MAP.keys())}",
            )

    plugins = PluginRegistry.list_plugins(plugin_type=ptype)
    return {
        "plugins": [
            {
                "plugin_id": p.plugin_id,
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "plugin_type": p.plugin_type.value,
                "author": p.author,
                "enabled": p.enabled,
            }
            for p in plugins
        ]
    }


@router.post("/register")
async def register_plugin(request: PluginRegisterRequest):
    """注册插件"""
    ptype = _TYPE_MAP.get(request.plugin_type)
    if ptype is None:
        raise HTTPException(
            status_code=400,
            detail=f"无效的插件类型: {request.plugin_type}，可选值: {list(_TYPE_MAP.keys())}",
        )

    info = PluginInfo(
        plugin_id=request.plugin_id,
        name=request.name,
        version=request.version,
        description=request.description,
        plugin_type=ptype,
        author=request.author,
        enabled=request.enabled,
    )

    success = PluginRegistry.register(info)
    if not success:
        raise HTTPException(status_code=409, detail=f"插件已存在: {request.plugin_id}")

    return {"status": "registered", "plugin_id": request.plugin_id}


@router.put("/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, request: PluginToggleRequest):
    """启用/禁用插件"""
    if request.enabled:
        success = PluginRegistry.enable(plugin_id)
    else:
        success = PluginRegistry.disable(plugin_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"插件不存在: {plugin_id}")

    return {"plugin_id": plugin_id, "enabled": request.enabled}


@router.delete("/{plugin_id}")
async def unregister_plugin(plugin_id: str):
    """注销插件"""
    success = PluginRegistry.unregister(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"插件不存在: {plugin_id}")

    return {"status": "unregistered", "plugin_id": plugin_id}


@router.get("/summary")
async def get_plugin_summary():
    """获取插件系统摘要"""
    return PluginManager.get_plugin_summary()


@router.get("/health")
async def plugins_health():
    """插件模块健康检查"""
    return {"status": "ok", "module": "plugins", "count": PluginRegistry.count()}
