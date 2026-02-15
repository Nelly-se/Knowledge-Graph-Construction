# src/graph_rag/rag_engine.py
from src.utils.logger import logger
from src.graph_rag.query_understanding import QueryParser
from src.graph_rag.graph_retriever import GraphRetriever
from src.graph_rag.llm_integration import LLMIntegration  # <--- 引入这个新管家

class RAGEngine:
    def __init__(self):
        logger.info("Initializing RAG Engine...")
        self.parser = QueryParser()
        self.retriever = GraphRetriever()
        
        # === 核心修改：不再自己连 OpenAI，而是请 LLMIntegration 管家 ===
        # 它会自动去 config.yaml 里找 api_key 和 model_name
        self.llm = LLMIntegration()

    def chat(self, user_query: str) -> dict:
        """
        处理用户提问，返回回答和参考上下文。
        """
        logger.info(f"Processing query: {user_query}")
        
        # 1. 意图识别与关键词提取
        # 注意：这里可能抛出异常，建议加个简单处理
        try:
            parsed_intent = self.parser.parse(user_query)
            logger.info(f"Parsed intent: {parsed_intent}")
        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            parsed_intent = {} # 降级处理
        
        # 2. 图谱检索
        try:
            context = self.retriever.retrieve(parsed_intent)
            logger.info(f"Retrieved context length: {len(context)}")
        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")
            context = "检索过程中出现错误，无法获取参考信息。"
        
        # 3. 构建 Prompt
        # 我们保留之前那个很棒的 System Prompt，防幻觉效果很好
        system_prompt = """
        你是一名资深的保险与医养专家，服务于泰康保险集团。你的职责是利用提供的专业知识库（Context）来回答客户关于保险产品、疾病医疗和养老机构的问题。

        *** 核心原则（必须严格遵守） ***
        1. **年龄合规性（最高优先级）**：
           - 用户会提供年龄（如 70岁）。你必须严格检查 Context 中保险产品的【投保年龄/承保年龄】。
           - 例子：如果产品写着“出生满28天-60周岁”，而用户是 70 岁，**绝对不能推荐**该产品。
           - 如果 Context 里所有的保险产品都超龄了，请直接回答：“很抱歉，知识库中暂无适合您当前年龄（{age}岁）的重疾/医疗险产品，建议关注防癌险或意外险。”
           - **严禁**把“最高续保年龄”（如105岁）当成“投保年龄”来忽悠用户。

        2. **险种匹配**：
           - 用户问“重疾险”，不要推荐“医疗险”。
           - 用户问“养老院”，不要推荐“保险”。

        3. **基于事实**：严格基于提供的 [Context] 信息回答。不要编造。
        4. **专业亲切**：语气要专业、温暖。
        """

        user_prompt = f"""
        [Context - 参考知识库]
        {context}

        [User Question - 用户问题]
        {user_query}

        请根据参考知识库回答用户问题：
        """

        # 4. 生成回答
        try:
            # === 核心修改：调用 LLMIntegration 的通用接口 ===
            # 这里不需要再传 model_name 了，管家自己知道
            answer = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3  # 保持低温，减少幻觉
            )
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            answer = "抱歉，系统暂时无法生成回答，请稍后再试。"

        return {
            "answer": answer,
            "context": context,
            "intent": parsed_intent
        }

    def close(self):
        self.retriever.close()
        # LLMIntegration 不需要显式关闭

if __name__ == "__main__":
    # 测试代码
    engine = RAGEngine()
    try:
        test_q = "70岁高血压老人推荐买什么保险？"
        result = engine.chat(test_q)
        print("\n=== 用户问题 ===")
        print(test_q)
        print("\n=== 参考知识 (Context) ===")
        print(result["context"])
        print("\n=== AI 回答 ===")
        print(result["answer"])
    finally:
        engine.close()