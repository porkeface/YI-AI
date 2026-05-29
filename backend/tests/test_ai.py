"""AI解释模块测试

测试覆盖：
- Prompt构建正确性
- LLM客户端配置与请求构建
- 解释器流程（mock LLM调用）
- 错误处理
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from foundation.types import (
    Element,
    Hexagram,
    Line,
    ProsperityState,
    RuleAnalysisResult,
    SixRelation,
    SixSpirit,
    Trigram,
    TrigramName,
    Verdict,
    YinYang,
)
from ai.llm_client import (
    LLMClient,
    LLMConfig,
    LLMAuthError,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from ai.interpreter import AIInterpreter
from ai.prompt_builder import PromptBuilder
from ai.config import LLM_CONFIGS, get_default_config


# ============================================================================
# 测试夹具（Fixtures）
# ============================================================================

@pytest.fixture
def sample_trigram_qian() -> Trigram:
    """乾卦三爻"""
    return Trigram(
        name=TrigramName.QIAN,
        binary_rep="111",
        element=Element.METAL,
        nature="天",
        direction="西北",
        family="父",
        body="头",
        animal="马",
    )


@pytest.fixture
def sample_trigram_kun() -> Trigram:
    """坤卦三爻"""
    return Trigram(
        name=TrigramName.KUN,
        binary_rep="000",
        element=Element.EARTH,
        nature="地",
        direction="西南",
        family="母",
        body="腹",
        animal="牛",
    )


@pytest.fixture
def sample_lines() -> tuple[Line, Line, Line, Line, Line, Line]:
    """六爻数据（天地否卦示例）"""
    return (
        Line(1, YinYang.YANG, False, Element.METAL, SixRelation.BROTHER,
             SixSpirit.QINGLONG, "甲子", False, False),
        Line(2, YinYang.YANG, False, Element.METAL, SixRelation.BROTHER,
             SixSpirit.ZHUQUE, "甲寅", False, False),
        Line(3, YinYang.YANG, True, Element.METAL, SixRelation.BROTHER,
             SixSpirit.GOUCHEN, "甲辰", True, False),
        Line(4, YinYang.YIN, False, Element.EARTH, SixRelation.PARENT,
             SixSpirit.TENGHE, "乙巳", False, False),
        Line(5, YinYang.YIN, False, Element.EARTH, SixRelation.PARENT,
             SixSpirit.BAIHU, "乙未", False, True),
        Line(6, YinYang.YIN, False, Element.EARTH, SixRelation.PARENT,
             SixSpirit.XUANWU, "乙酉", False, False),
    )


@pytest.fixture
def sample_hexagram(
    sample_trigram_qian: Trigram,
    sample_trigram_kun: Trigram,
    sample_lines: tuple[Line, Line, Line, Line, Line, Line],
) -> Hexagram:
    """天地否卦"""
    return Hexagram(
        id=12,
        name="天地否",
        upper_trigram=sample_trigram_qian,
        lower_trigram=sample_trigram_kun,
        lines=sample_lines,
        element=Element.METAL,
        judgment="否之匪人，不利君子贞，大往小来。",
        image="天地不交，否。君子以俭德辟难，不可荣以禄。",
    )


@pytest.fixture
def sample_analysis() -> RuleAnalysisResult:
    """规则分析结果示例"""
    return RuleAnalysisResult(
        yong_shen=SixRelation.WEALTH,
        moving_lines=(3,),
        relationships=(
            "用神(金)月令旺：当令而旺",
            "用神对世爻：生",
            "三爻动化回头生",
        ),
        prosperity=ProsperityState.WANG,
        verdict=Verdict(overall="吉", strength=75, trend="上升", confidence=60),
    )


@pytest.fixture
def llm_config() -> LLMConfig:
    """测试用LLM配置"""
    return LLMConfig(
        provider="deepseek",
        api_key="test-api-key-12345",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )


@pytest.fixture
def llm_client(llm_config: LLMConfig) -> LLMClient:
    """测试用LLM客户端"""
    return LLMClient(llm_config)


@pytest.fixture
def interpreter(llm_client: LLMClient) -> AIInterpreter:
    """测试用AI解释器"""
    return AIInterpreter(llm_client)


# ============================================================================
# Prompt构建器测试
# ============================================================================

class TestPromptBuilder:
    """PromptBuilder测试"""

    def test_system_prompt_contains_core_principles(self) -> None:
        """系统提示词应包含核心原则"""
        builder = PromptBuilder()
        prompt = builder.build_system_prompt()

        assert "易学" in prompt
        assert "通俗易懂" in prompt
        assert "趋势" in prompt
        # 系统提示词会提到"算命"作为禁用词示例，这是正确的
        assert "不要使用" in prompt
        assert "中性词" in prompt

    def test_user_prompt_contains_question(
        self,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """用户提示词应包含用户问题"""
        builder = PromptBuilder()
        question = "我最近的事业运势如何？"
        prompt = builder.build_user_prompt(
            question, sample_hexagram, sample_analysis
        )

        assert question in prompt

    def test_user_prompt_contains_hexagram_info(
        self,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """用户提示词应包含卦象信息"""
        builder = PromptBuilder()
        prompt = builder.build_user_prompt(
            "测试问题", sample_hexagram, sample_analysis
        )

        assert "天地否" in prompt
        assert "乾" in prompt
        assert "坤" in prompt
        assert sample_hexagram.judgment in prompt

    def test_user_prompt_contains_analysis(
        self,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """用户提示词应包含分析结果"""
        builder = PromptBuilder()
        prompt = builder.build_user_prompt(
            "测试问题", sample_hexagram, sample_analysis
        )

        assert "妻财" in prompt  # 用神
        assert "旺" in prompt    # 旺衰
        assert "吉" in prompt    # 结论
        assert "75" in prompt    # 强度

    def test_user_prompt_contains_line_details(
        self,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """用户提示词应包含六爻详情"""
        builder = PromptBuilder()
        prompt = builder.build_user_prompt(
            "测试问题", sample_hexagram, sample_analysis
        )

        assert "初爻" in prompt
        assert "上爻" in prompt
        assert "动爻" in prompt
        assert "[世]" in prompt
        assert "[应]" in prompt

    def test_user_prompt_contains_instruction(
        self,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """用户提示词应包含生成指令"""
        builder = PromptBuilder()
        prompt = builder.build_user_prompt(
            "测试问题", sample_hexagram, sample_analysis
        )

        assert "通俗易懂" in prompt

    def test_position_name_mapping(self) -> None:
        """爻位名称映射正确"""
        builder = PromptBuilder()
        assert builder._position_name(1) == "初爻"
        assert builder._position_name(2) == "二爻"
        assert builder._position_name(6) == "上爻"
        assert "7" in builder._position_name(7)  # 越界回退


# ============================================================================
# LLM客户端测试
# ============================================================================

class TestLLMConfig:
    """LLMConfig测试"""

    def test_config_is_frozen(self, llm_config: LLMConfig) -> None:
        """配置应为不可变对象"""
        with pytest.raises(AttributeError):
            llm_config.provider = "qwen"  # type: ignore[misc]

    def test_config_default_values(self) -> None:
        """配置应有合理的默认值"""
        config = LLMConfig(
            provider="test",
            api_key="key",
            base_url="https://example.com",
            model="test-model",
        )
        assert config.max_tokens == 2000
        assert config.temperature == 0.7


class TestLLMClient:
    """LLMClient测试"""

    def test_payload_construction(self, llm_client: LLMClient) -> None:
        """请求体构建正确"""
        payload = llm_client._build_payload(
            "系统提示", "用户提示", stream=False
        )

        assert payload["model"] == "deepseek-chat"
        assert payload["stream"] is False
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 2000

        messages = payload["messages"]  # type: ignore[index]
        assert len(messages) == 2  # type: ignore[arg-type]
        assert messages[0]["role"] == "system"  # type: ignore[index]
        assert messages[0]["content"] == "系统提示"  # type: ignore[index]
        assert messages[1]["role"] == "user"  # type: ignore[index]
        assert messages[1]["content"] == "用户提示"  # type: ignore[index]

    def test_stream_payload(self, llm_client: LLMClient) -> None:
        """流式请求体正确"""
        payload = llm_client._build_payload("s", "u", stream=True)
        assert payload["stream"] is True

    def test_check_status_200(self) -> None:
        """200状态码不抛异常"""
        response = MagicMock()
        response.status_code = 200
        LLMClient._check_status(response)  # type: ignore[arg-type]

    def test_check_status_401(self) -> None:
        """401抛出认证异常"""
        response = MagicMock()
        response.status_code = 401
        with pytest.raises(LLMAuthError):
            LLMClient._check_status(response)  # type: ignore[arg-type]

    def test_check_status_429(self) -> None:
        """429抛出限流异常"""
        response = MagicMock()
        response.status_code = 429
        with pytest.raises(LLMRateLimitError):
            LLMClient._check_status(response)  # type: ignore[arg-type]

    def test_check_status_500(self) -> None:
        """500抛出通用异常"""
        response = MagicMock()
        response.status_code = 500
        with pytest.raises(LLMError):
            LLMClient._check_status(response)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_chat_success(self, llm_client: LLMClient) -> None:
        """正常调用返回结果"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "这是AI的解释"}}]
        }

        with patch.object(
            llm_client._client, "post", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await llm_client.chat("系统", "用户")
            assert result == "这是AI的解释"

    @pytest.mark.asyncio
    async def test_chat_strips_whitespace(
        self, llm_client: LLMClient
    ) -> None:
        """返回结果应去除首尾空白"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "  结果  "}}]
        }

        with patch.object(
            llm_client._client, "post", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await llm_client.chat("s", "u")
            assert result == "结果"

    @pytest.mark.asyncio
    async def test_chat_timeout_raises(
        self, llm_client: LLMClient
    ) -> None:
        """超时应抛出LLMTimeoutError"""
        import httpx

        with patch.object(
            llm_client._client, "post", new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(LLMTimeoutError):
                await llm_client.chat("s", "u")

    @pytest.mark.asyncio
    async def test_chat_auth_error(self, llm_client: LLMClient) -> None:
        """认证失败应抛出LLMAuthError"""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(
            llm_client._client, "post", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(LLMAuthError):
                await llm_client.chat("s", "u")

    @pytest.mark.asyncio
    async def test_chat_invalid_response(
        self, llm_client: LLMClient
    ) -> None:
        """响应格式异常应抛出LLMResponseError"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "format"}

        with patch.object(
            llm_client._client, "post", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(LLMResponseError):
                await llm_client.chat("s", "u")


# ============================================================================
# AI解释器测试
# ============================================================================

class TestAIInterpreter:
    """AIInterpreter测试"""

    @pytest.mark.asyncio
    async def test_interpret_calls_llm(
        self,
        interpreter: AIInterpreter,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """interpret应调用LLM并返回结果"""
        mock_result = "这是一段卦象解释..."

        with patch.object(
            interpreter.llm_client, "chat",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_chat:
            result = await interpreter.interpret(
                "我的事业如何？", sample_hexagram, sample_analysis
            )

            assert result == mock_result
            mock_chat.assert_called_once()

            # 验证传入的参数
            call_args = mock_chat.call_args
            system_prompt = call_args[0][0]
            user_prompt = call_args[0][1]

            assert "易学" in system_prompt
            assert "我的事业如何？" in user_prompt

    @pytest.mark.asyncio
    async def test_interpret_propagates_llm_error(
        self,
        interpreter: AIInterpreter,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """LLM错误应向上抛出"""
        with patch.object(
            interpreter.llm_client, "chat",
            new_callable=AsyncMock,
            side_effect=LLMTimeoutError("timeout"),
        ):
            with pytest.raises(LLMTimeoutError):
                await interpreter.interpret(
                    "问题", sample_hexagram, sample_analysis
                )

    @pytest.mark.asyncio
    async def test_interpret_stream_yields_chunks(
        self,
        interpreter: AIInterpreter,
        sample_hexagram: Hexagram,
        sample_analysis: RuleAnalysisResult,
    ) -> None:
        """流式调用应逐步产出文本片段"""
        chunks = ["你好", "，这", "是解释", "。"]

        async def mock_stream(*args, **kwargs):  # type: ignore[no-untyped-def]
            for chunk in chunks:
                yield chunk

        with patch.object(
            interpreter.llm_client, "chat_stream",
            side_effect=mock_stream,
        ):
            collected: list[str] = []
            async for chunk in interpreter.interpret_stream(
                "问题", sample_hexagram, sample_analysis
            ):
                collected.append(chunk)

            assert collected == chunks


# ============================================================================
# 配置模块测试
# ============================================================================

class TestConfig:
    """AI配置测试"""

    def test_llm_configs_contains_providers(self) -> None:
        """配置字典应包含支持的提供商"""
        assert "deepseek" in LLM_CONFIGS
        assert "qwen" in LLM_CONFIGS

    def test_deepseek_config(self) -> None:
        """DeepSeek配置正确"""
        config = LLM_CONFIGS["deepseek"]
        assert config.provider == "deepseek"
        assert "deepseek.com" in config.base_url
        assert config.model == "deepseek-chat"

    def test_qwen_config(self) -> None:
        """Qwen配置正确"""
        config = LLM_CONFIGS["qwen"]
        assert config.provider == "qwen"
        assert "dashscope" in config.base_url
        assert config.model == "qwen-turbo"

    def test_get_default_config_missing_key(self) -> None:
        """API Key为空时应抛出异常"""
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}, clear=False):
            # 重新读取配置
            from ai import config as config_module
            original_key = config_module.LLM_CONFIGS["deepseek"].api_key
            try:
                config_module.LLM_CONFIGS["deepseek"] = LLMConfig(
                    provider="deepseek",
                    api_key="",
                    base_url="https://api.deepseek.com/v1",
                    model="deepseek-chat",
                )
                with pytest.raises(ValueError, match="环境变量"):
                    config_module.get_default_config()
            finally:
                config_module.LLM_CONFIGS["deepseek"] = LLMConfig(
                    provider="deepseek",
                    api_key=original_key,
                    base_url="https://api.deepseek.com/v1",
                    model="deepseek-chat",
                )
