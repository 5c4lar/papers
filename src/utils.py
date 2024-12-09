from typing import Any, Dict, List

import aisuite as ai

from src.config import ModelConfig, OpenaiConfig, AisuiteConfig


def call_llm(
    messages: List[Dict[str, Any]] = [],
    **kwargs,
):
    provider_configs = {
        "openai": {
            "base_url": OpenaiConfig.base_url,
            "api_key": OpenaiConfig.api_key,
        },
    }
    client = ai.Client(provider_configs=provider_configs)

    params = {k: getattr(ModelConfig, k) for k in ModelConfig.__annotations__}
    params.update(kwargs)

    response = client.chat.completions.create(
        model=AisuiteConfig.model_name,
        messages=messages,
        **params,
    )

    return response.choices[0].message.content
