
import os  # <--- 新增：引入系统模块
from typing import List, Dict, Any, Optional, Generator
from src.utils.config_loader import config
from src.utils.logger import logger
from dotenv import load_dotenv # <--- 新增：确保加载 .env

# 强制加载一次环境变量
load_dotenv()

class LLMIntegration:
    """大模型集成：优先读 config，其次读环境变量。"""

    def __init__(self):
        llm_conf = config.get("llm", {})
        
        self.model_type = llm_conf.get("model_type", "api")
        self.model_name = llm_conf.get("model_name", "qwen-turbo")
        self.api_base = llm_conf.get("api_base")
        
        # === 核心修改：双重保险机制 ===
        # 1. 尝试从 config.yaml 读
        # 2. 如果没有，尝试从环境变量 (.env) 读 DASHSCOPE_API_KEY
        self.api_key = llm_conf.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
        
        # 同样的逻辑也可以用于 Neo4j 密码（虽然这里只处理 LLM）
        
        self._client = None
        
        # 调试日志：只打印前几位，防止泄露
        masked_key = (self.api_key[:8] + "...") if self.api_key else "未找到!"
        logger.info(f"LLM Init: Model={self.model_name}, Key={masked_key}")

    # ... (后面的代码 _get_client, chat, generate 等保持不变) ...
    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
            if not self.api_key:
                logger.error("❌ 致命错误: 未找到 API Key！请检查 config.yaml 或 .env 文件")
            
            self._client = OpenAI(
                api_key=self.api_key, 
                base_url=self.api_base
            )
            return self._client
        except Exception as e:
            logger.error(f"LLM 客户端初始化失败: {e}")
            raise
    
    # 下面的 chat 和 generate 函数直接复用之前的即可，不用改
    def chat(self, messages, temperature=0.3, max_tokens=None, **kwargs):
        if self.model_type == "api":
            try:
                client = self._get_client()
                resp = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens or 1024,
                    **kwargs,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception as e:
                logger.error(f"调用大模型 API 失败: {e}")
                return "抱歉，系统暂时无法生成回答 (LLM API Error)。"
        return "非 API 模式"

    def generate(self, prompt, system_prompt=None, temperature=0.3, **kwargs):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, **kwargs)