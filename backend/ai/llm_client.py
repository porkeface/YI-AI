"""LLM API客户端模块

封装对DeepSeek/Qwen等兼容OpenAI格式的LLM API调用。
支持同步调用和流式调用（SSE）。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# 配置数据类
# ============================================================================

@dataclass(frozen=True)
class LLMConfig:
    """LLM配置

    Attributes:
        provider: 提供商名称（deepseek / qwen）
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        max_tokens: 最大生成token数
        temperature: 温度参数（0-2，越高越随机）
    """
    provider: str
    api_key: str
    base_url: str
    model: str
    max_tokens: int = 2000
    temperature: float = 0.7


# ============================================================================
# 异常定义
# ============================================================================

class LLMError(Exception):
    """LLM调用异常基类"""


class LLMAuthError(LLMError):
    """认证失败（API Key无效）"""


class LLMRateLimitError(LLMError):
    """请求频率超限"""


class LLMTimeoutError(LLMError):
    """请求超时"""


class LLMResponseError(LLMError):
    """响应格式错误"""


# ============================================================================
# LLM客户端
# ============================================================================

class LLMClient:
    """LLM API客户端

    封装对兼容OpenAI格式的LLM API调用。
    """

    def __init__(self, config: LLMConfig) -> None:
        """初始化客户端

        Args:
            config: LLM配置
        """
        self.config = config
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "api-key": config.api_key,
                "Content-Type": "application/json",
            },
        )

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM API（非流式）

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            LLM生成的文本

        Raises:
            LLMError: 调用失败
        """
        payload = self._build_payload(system_prompt, user_prompt, stream=False)

        try:
            response = await self._client.post(
                f"{self.config.base_url}/chat/completions",
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LLM API请求超时") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM API请求失败: {exc}") from exc

        self._check_status(response)

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMResponseError(f"LLM响应格式异常: {exc}") from exc

        return content.strip()

    async def chat_stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncIterator[str]:
        """流式调用LLM API（SSE）

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Yields:
            逐步生成的文本片段

        Raises:
            LLMError: 调用失败
        """
        payload = self._build_payload(system_prompt, user_prompt, stream=True)

        try:
            async with self._client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                json=payload,
            ) as response:
                self._check_status(response)

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[len("data: "):]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        # 跳过格式异常的单个chunk，不中断流
                        logger.debug("跳过格式异常的SSE chunk: %s", data_str)
                        continue

        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LLM API流式请求超时") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM API流式请求失败: {exc}") from exc

    async def close(self) -> None:
        """关闭HTTP客户端"""
        await self._client.aclose()

    async def __aenter__(self) -> LLMClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        stream: bool = False,
    ) -> dict[str, object]:
        """构建请求体

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            stream: 是否流式

        Returns:
            请求体字典
        """
        return {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": stream,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

    @staticmethod
    def _check_status(response: httpx.Response) -> None:
        """检查HTTP状态码并抛出对应异常

        Args:
            response: HTTP响应对象

        Raises:
            LLMAuthError: 401
            LLMRateLimitError: 429
            LLMError: 其他非200
        """
        if response.status_code == 200:
            return

        if response.status_code == 401:
            raise LLMAuthError("API Key无效或已过期")
        if response.status_code == 429:
            raise LLMRateLimitError("请求频率超限，请稍后重试")

        raise LLMError(
            f"LLM API返回错误状态码 {response.status_code}"
        )
