"""知识图谱API

提供图谱数据查询接口，供前端 Cytoscape.js 可视化使用。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel

from api.schemas import ApiResponse
from ai.knowledge_graph import KnowledgeGraph

logger = structlog.get_logger()
router = APIRouter(prefix="/api/graph", tags=["graph"])

# 全局图谱实例（延迟初始化）
_graph: KnowledgeGraph | None = None


def _get_graph() -> KnowledgeGraph:
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
    return _graph


class GraphData(BaseModel):
    """图谱数据（Cytoscape.js 格式）"""
    nodes: list[dict]
    edges: list[dict]


@router.get("/", response_model=ApiResponse)
async def get_graph_data(
    node_type: str | None = Query(None, description="按节点类型过滤"),
    limit: int = Query(200, ge=1, le=1000, description="最大节点数"),
):
    """获取图谱数据（Cytoscape.js 格式）"""
    graph = _get_graph()

    nodes = []
    edges = []
    edge_id = 0

    for nid, node in graph._backend._nodes.items():
        if node_type and node["type"] != node_type:
            continue
        if len(nodes) >= limit:
            break

        nodes.append({
            "data": {
                "id": nid,
                "label": node["properties"].get("name", nid),
                "type": node["type"],
                **{k: v for k, v in node["properties"].items() if k != "name"},
            }
        })

    # 收集已选中节点的边
    node_ids = {n["data"]["id"] for n in nodes}
    for (src, tgt), edges_list in graph._backend._edges.items():
        if src in node_ids and tgt in node_ids:
            for edge in edges_list:
                edge_id += 1
                edges.append({
                    "data": {
                        "id": f"e{edge_id}",
                        "source": src,
                        "target": tgt,
                        "relation": edge["relation"],
                        **edge.get("properties", {}),
                    }
                })

    return ApiResponse(success=True, data=GraphData(nodes=nodes, edges=edges).model_dump())


@router.get("/node/{node_id}", response_model=ApiResponse)
async def get_node_detail(node_id: str):
    """获取节点详情及其邻居"""
    graph = _get_graph()

    node = graph._backend.get_node(node_id)
    if not node:
        return ApiResponse(success=False, error=f"节点不存在: {node_id}")

    neighbors = graph._backend.get_neighbors(node_id)

    return ApiResponse(success=True, data={
        "node": {
            "id": node_id,
            "type": node["type"],
            **node["properties"],
        },
        "neighbors": [
            {
                "id": n["id"],
                "type": n["type"],
                **n.get("properties", {}),
            }
            for n in neighbors
        ],
    })


@router.get("/stats", response_model=ApiResponse)
async def get_graph_stats():
    """获取图谱统计信息"""
    graph = _get_graph()
    backend = graph._backend

    type_counts: dict[str, int] = {}
    for node in backend._nodes.values():
        t = node["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    edge_count = sum(len(v) for v in backend._edges.values())

    return ApiResponse(success=True, data={
        "nodeCount": len(backend._nodes),
        "edgeCount": edge_count,
        "typeCounts": type_counts,
    })
