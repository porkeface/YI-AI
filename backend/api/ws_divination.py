"""WebSocket 流式起卦端点

提供 WebSocket 连接，实现 AI 解读的流式输出。
客户端发送起卦请求，服务端逐 chunk 返回 AI 解读文本。

协议：
- 客户端发送: JSON { question, method, ... }
- 服务端发送: JSON { type: "chunk", content: "..." }
- 服务端发送: JSON { type: "done" }
- 服务端发送: JSON { type: "error", message: "..." }
"""

from __future__ import annotations

import json
import logging

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.divination import (
    _extract_question_type,
    _enrich_hexagram,
    _generate_lines_from_time,
    _generate_lines_from_numbers,
    _generate_lines_from_manual,
    _hexagram_to_response,
    _format_analysis,
    _get_ai_interpreter,
    _get_current_gan_zhi,
)
from api.schemas import DivinationRequest
from foundation.hexagram_engine import HexagramEngine
from rule_engine.analyzer import Analyzer

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/ws/divination")
async def websocket_divination(websocket: WebSocket):
    """WebSocket 流式起卦

    接收起卦请求，执行排盘和规则分析后，
    通过 WebSocket 流式返回 AI 解读。
    """
    await websocket.accept()
    logger.info("ws_client_connected")

    try:
        while True:
            # 接收客户端消息
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的JSON格式",
                })
                continue

            # 解析请求
            try:
                request = DivinationRequest(**payload)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"请求参数错误: {e}",
                })
                continue

            # 执行起卦流程
            await _process_divination_ws(websocket, request)

    except WebSocketDisconnect:
        logger.info("ws_client_disconnected")
    except Exception as e:
        logger.error("ws_unexpected_error", error=str(e), exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "服务器内部错误",
            })
        except Exception:
            pass


async def _process_divination_ws(
    websocket: WebSocket,
    request: DivinationRequest,
) -> None:
    """处理起卦请求（WebSocket 版本）

    执行完整的起卦流程，并通过 WebSocket 流式返回 AI 解读。
    """
    # 1. 生成阴阳值和动爻
    if request.method == "time":
        yin_yangs, moving_positions = _generate_lines_from_time()
    elif request.method == "number":
        if not request.numbers or len(request.numbers) < 2:
            await websocket.send_json({
                "type": "error",
                "message": "数字起卦需要提供两个数字",
            })
            return
        yin_yangs, moving_positions = _generate_lines_from_numbers(
            request.numbers
        )
    elif request.method == "manual":
        if not request.manual_lines or len(request.manual_lines) != 6:
            await websocket.send_json({
                "type": "error",
                "message": "手动排盘需要提供6个阴阳值",
            })
            return
        yin_yangs, moving_positions = _generate_lines_from_manual(
            request.manual_lines, request.moving_positions
        )
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"不支持的起卦方式: {request.method}",
        })
        return

    # 2. 创建基础卦
    try:
        hexagram = HexagramEngine.create(yin_yangs)
    except ValueError as e:
        await websocket.send_json({
            "type": "error",
            "message": f"创建卦失败: {e}",
        })
        return

    # 3. 获取当前干支
    day_stem, month_branch = _get_current_gan_zhi()

    # 4. 充实卦数据
    enriched_hexagram = _enrich_hexagram(hexagram, moving_positions, day_stem)

    # 5. 计算变卦
    changed_hexagram = None
    if moving_positions:
        try:
            changed = HexagramEngine.get_changed(
                hexagram, tuple(moving_positions)
            )
            changed_hexagram = _enrich_hexagram(changed, [], day_stem)
        except (ValueError, IndexError):
            changed_hexagram = None

    # 6. 规则分析
    question_type = _extract_question_type(request.question)
    try:
        analysis_result = Analyzer.analyze(
            enriched_hexagram, question_type, month_branch
        )
    except Exception:
        from api.divination import _default_analysis_result
        analysis_result = _default_analysis_result(moving_positions)

    # 7. 先发送排盘结果
    hexagram_response = _hexagram_to_response(enriched_hexagram)
    changed_response = (
        _hexagram_to_response(changed_hexagram)
        if changed_hexagram
        else None
    )
    analysis_response = _format_analysis(analysis_result, enriched_hexagram)

    await websocket.send_json({
        "type": "result",
        "data": {
            "hexagram": hexagram_response,
            "changedHexagram": changed_response,
            "analysis": analysis_response,
        },
    })

    # 8. 流式 AI 解读
    interpreter = _get_ai_interpreter()
    if interpreter is None:
        await websocket.send_json({
            "type": "done",
            "aiInterpretation": None,
        })
        return

    try:
        from ai.safety_checker import check_safety

        full_text = ""
        async for chunk in interpreter.interpret_stream(
            request.question,
            enriched_hexagram,
            analysis_result,
            question_type,
        ):
            full_text += chunk
            await websocket.send_json({
                "type": "chunk",
                "content": chunk,
            })

        # 安全检查
        check_result = check_safety(full_text)

        await websocket.send_json({
            "type": "done",
            "aiInterpretation": check_result.text,
        })

    except Exception as e:
        logger.warning("ws_ai_stream_failed", error=str(e))
        await websocket.send_json({
            "type": "done",
            "aiInterpretation": None,
        })
