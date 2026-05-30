"""知识图谱API

提供图谱数据查询接口，供前端 Cytoscape.js 可视化使用。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel

from api.schemas import ApiResponse
from ai.knowledge_graph import KnowledgeGraph, NodeType

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
    backend = graph._backend

    nodes = []
    edges = []
    edge_id = 0

    # Use query_by_type for filtering, or get all types
    if node_type:
        try:
            nt = NodeType(node_type)
            all_nodes = backend.query_by_type(nt)
        except ValueError:
            all_nodes = ()
    else:
        all_nodes = []
        for nt in NodeType:
            all_nodes.extend(backend.query_by_type(nt))

    # Apply limit
    limited_nodes = list(all_nodes)[:limit]
    node_ids = set()

    for node in limited_nodes:
        node_ids.add(node.id)
        nodes.append({
            "data": {
                "id": node.id,
                "label": node.name,
                "type": node.node_type.value,
                **{k: v for k, v in node.properties.items() if k != "name"},
            }
        })

    # Get edges between selected nodes using get_edges
    all_edges = backend.get_edges()
    for edge in all_edges:
        if edge.source_id in node_ids and edge.target_id in node_ids:
            edge_id += 1
            edges.append({
                "data": {
                    "id": f"e{edge_id}",
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "relation": edge.relation.value,
                    **edge.properties,
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
            "type": node.node_type.value,
            **node.properties,
        },
        "neighbors": [
            {
                "id": n.id,
                "type": n.node_type.value,
                **n.properties,
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
    total_nodes = 0
    for nt in NodeType:
        nodes = backend.query_by_type(nt)
        count = len(nodes)
        if count > 0:
            type_counts[nt.value] = count
        total_nodes += count

    all_edges = backend.get_edges()
    edge_count = len(all_edges)

    return ApiResponse(success=True, data={
        "nodeCount": total_nodes,
        "edgeCount": edge_count,
        "typeCounts": type_counts,
    })
