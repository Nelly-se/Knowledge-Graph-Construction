# 大模型集成：Qwen 本地 / 百炼 API（OpenAI 兼容）
from typing import List, Dict, Any, Optional, Generator


class LLMIntegration:
    """大模型集成：统一封装本地模型与云端 API。"""

    def __init__(
        self,
        model_type: str = "local",
        model_path: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs: Any,
    ):
        self.model_type = model_type
        self.model_path = model_path
        self.api_key = api_key
        self.api_base = api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 百炼兼容
        self.model_name = model_name or "qwen-turbo"
        self._client = None

    def _get_client(self):
        """懒加载 OpenAI 兼容客户端（用于 api 模式）。"""
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key or "dummy", base_url=self.api_base)
            return self._client
        except Exception as e:
            raise RuntimeError(f"LLM 客户端初始化失败: {e}") from e

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """多轮对话式生成。"""
        if self.model_type == "api" and self.api_key and self.api_key != "your_api_key":
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 1024,
                **kwargs,
            )
            return (resp.choices[0].message.content or "").strip()
        return "（当前为未配置或本地模式，仅返回占位。请在 config.yaml 中配置 llm.model_type=api 与 api_key 后使用百炼等 API。）"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """单轮生成（RAG 问答）。"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """流式生成（可选）。"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        if self.model_type == "api" and self.api_key and self.api_key != "your_api_key":
            client = self._get_client()
            stream = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                **kwargs,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield self.generate(prompt, system_prompt=system_prompt, **kwargs)
