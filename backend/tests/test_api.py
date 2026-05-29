"""API集成测试

测试所有API端点的功能和错误处理。
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import app


@pytest.fixture
async def client():
    """创建异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ============================================================================
# 健康检查
# ============================================================================


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# ============================================================================
# 起卦接口
# ============================================================================


@pytest.mark.asyncio
async def test_time_divination(client: AsyncClient):
    """测试时间起卦"""
    response = await client.post(
        "/api/divination/",
        json={"question": "今日运势如何？", "method": "time"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is not None

    hexagram = data["data"]["hexagram"]
    assert hexagram["id"] > 0
    assert len(hexagram["name"]) > 0
    assert len(hexagram["lines"]) == 6
    assert hexagram["element"] in ("金", "木", "水", "火", "土")

    # 验证每爻数据完整性
    for line in hexagram["lines"]:
        assert line["position"] in range(1, 7)
        assert line["yinYang"] in ("yin", "yang")
        assert isinstance(line["isMoving"], bool)
        assert line["element"] in ("金", "木", "水", "火", "土")
        assert len(line["sixRelation"]) > 0
        assert len(line["sixSpirit"]) > 0
        assert isinstance(line["ganZhi"], dict)
        assert len(line["ganZhi"]["gan"]) > 0
        assert len(line["ganZhi"]["zhi"]) > 0

    # 验证分析结果
    analysis = data["data"]["analysis"]
    assert len(analysis["fortune"]) > 0
    assert isinstance(analysis["keyPoints"], list)
    assert len(analysis["summary"]) > 0


@pytest.mark.asyncio
async def test_number_divination(client: AsyncClient):
    """测试数字起卦"""
    response = await client.post(
        "/api/divination/",
        json={"question": "财运如何？", "method": "number", "numbers": [3, 5]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is not None

    hexagram = data["data"]["hexagram"]
    assert hexagram["id"] > 0
    assert len(hexagram["lines"]) == 6

    # 3 % 8 = 3 -> 离(101), 5 % 8 = 5 -> 巽(011)
    # lower=101(离), upper=011(巽) -> binary=101011
    # (3+5) % 6 + 1 = 3 -> 动爻在第3位
    assert hexagram["lines"][2]["isMoving"] is True


@pytest.mark.asyncio
async def test_manual_divination(client: AsyncClient):
    """测试手动排盘"""
    response = await client.post(
        "/api/divination/",
        json={
            "question": "事业前景如何？",
            "method": "manual",
            "manual_lines": [1, 1, 1, 1, 1, 1],  # 乾为天
            "moving_positions": [1, 6],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is not None

    hexagram = data["data"]["hexagram"]
    assert hexagram["name"] == "乾为天"
    assert len(hexagram["lines"]) == 6

    # 验证动爻
    assert hexagram["lines"][0]["isMoving"] is True  # 第1爻
    assert hexagram["lines"][5]["isMoving"] is True  # 第6爻
    assert hexagram["lines"][1]["isMoving"] is False  # 第2爻不动

    # 有动爻时应有变卦
    assert data["data"]["changedHexagram"] is not None


@pytest.mark.asyncio
async def test_manual_divination_without_moving(client: AsyncClient):
    """测试手动排盘不指定动爻（使用时间推算）"""
    response = await client.post(
        "/api/divination/",
        json={
            "question": "测试",
            "method": "manual",
            "manual_lines": [0, 0, 0, 0, 0, 0],  # 坤为地
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["hexagram"]["name"] == "坤为地"


# ============================================================================
# 错误处理
# ============================================================================


@pytest.mark.asyncio
async def test_number_divination_missing_numbers(client: AsyncClient):
    """测试数字起卦缺少数字"""
    response = await client.post(
        "/api/divination/",
        json={"question": "测试", "method": "number"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "数字" in data["error"]


@pytest.mark.asyncio
async def test_number_divination_not_enough_numbers(client: AsyncClient):
    """测试数字起卦数字不足"""
    response = await client.post(
        "/api/divination/",
        json={"question": "测试", "method": "number", "numbers": [3]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "数字" in data["error"]


@pytest.mark.asyncio
async def test_manual_divination_invalid_lines(client: AsyncClient):
    """测试手动排盘无效阴阳值"""
    response = await client.post(
        "/api/divination/",
        json={
            "question": "测试",
            "method": "manual",
            "manual_lines": [1, 0, 2, 1, 0, 1],  # 2是无效值
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "阴阳" in data["error"]


@pytest.mark.asyncio
async def test_manual_divination_wrong_count(client: AsyncClient):
    """测试手动排盘数量不对"""
    response = await client.post(
        "/api/divination/",
        json={
            "question": "测试",
            "method": "manual",
            "manual_lines": [1, 0, 1],  # 只有3个
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "6" in data["error"]


@pytest.mark.asyncio
async def test_invalid_method(client: AsyncClient):
    """测试无效起卦方式"""
    response = await client.post(
        "/api/divination/",
        json={"question": "测试", "method": "invalid"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "不支持" in data["error"]


# ============================================================================
# 起卦方式列表
# ============================================================================


@pytest.mark.asyncio
async def test_get_methods(client: AsyncClient):
    """测试获取起卦方式列表"""
    response = await client.get("/api/divination/methods")
    assert response.status_code == 200
    data = response.json()
    assert "methods" in data
    assert len(data["methods"]) == 3

    values = [m["value"] for m in data["methods"]]
    assert "time" in values
    assert "number" in values
    assert "manual" in values


# ============================================================================
# 卦象查询
# ============================================================================


@pytest.mark.asyncio
async def test_list_hexagrams(client: AsyncClient):
    """测试获取64卦列表"""
    response = await client.get("/api/hexagram/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 64

    # 验证第一卦
    first = data["data"][0]
    assert first["id"] == 1
    assert first["name"] == "乾为天"


@pytest.mark.asyncio
async def test_get_hexagram(client: AsyncClient):
    """测试获取单个卦详情"""
    response = await client.get("/api/hexagram/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    hexagram = data["data"]
    assert hexagram["id"] == 1
    assert hexagram["name"] == "乾为天"
    assert hexagram["upperTrigram"] == "乾"
    assert hexagram["lowerTrigram"] == "乾"
    assert hexagram["element"] == "金"
    assert hexagram["judgment"] == "元亨利贞"
    assert len(hexagram["lines"]) == 6


@pytest.mark.asyncio
async def test_get_hexagram_second(client: AsyncClient):
    """测试获取坤卦详情"""
    response = await client.get("/api/hexagram/2")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "坤为地"
    assert data["data"]["element"] == "土"


@pytest.mark.asyncio
async def test_get_hexagram_invalid_id(client: AsyncClient):
    """测试获取无效卦ID"""
    response = await client.get("/api/hexagram/99")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] is not None


@pytest.mark.asyncio
async def test_search_hexagram(client: AsyncClient):
    """测试按名称搜索卦"""
    response = await client.get("/api/hexagram/search/乾")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0

    names = [h["name"] for h in data["data"]]
    assert any("乾" in name for name in names)


@pytest.mark.asyncio
async def test_search_hexagram_no_result(client: AsyncClient):
    """测试搜索不存在的卦名"""
    response = await client.get("/api/hexagram/search/不存在的卦")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 0
