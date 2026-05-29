"""AI配置模块

管理LLM提供商配置，API Key从环境变量读取。
"""

from __future__ import annotations

import os

from ai.llm_client import LLMConfig


# LLM配置字典
LLM_CONFIGS: dict[str, LLMConfig] = {
    "deepseek": LLMConfig(
        provider="deepseek",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
    ),
    "qwen": LLMConfig(
        provider="qwen",
        api_key=os.getenv("QWEN_API_KEY", ""),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-turbo",
    ),
}

# 默认LLM提供商
DEFAULT_LLM: str = os.getenv("DEFAULT_LLM", "deepseek")


def get_default_config() -> LLMConfig:
    """获取默认LLM配置

    Returns:
        默认LLM配置对象

    Raises:
        ValueError: 未找到默认配置或API Key为空
    """
    config = LLM_CONFIGS.get(DEFAULT_LLM)
    if config is None:
        raise ValueError(f"未知的LLM提供商: {DEFAULT_LLM}")

    if not config.api_key:
        env_key = f"{DEFAULT_LLM.upper()}_API_KEY"
        raise ValueError(
            f"请设置环境变量 {env_key} 以使用 {DEFAULT_LLM} 提供商"
        )

    return config
