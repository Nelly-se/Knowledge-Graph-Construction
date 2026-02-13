from openai import OpenAI
from src.utils.config_loader import config
from src.utils.logger import logger
from src.graph_rag.query_understanding import QueryParser
from src.graph_rag.graph_retriever import GraphRetriever

class RAGEngine:
    def __init__(self):
        self.parser = QueryParser()
        self.retriever = GraphRetriever()
        
        self.api_key = config.get("OPENAI_API_KEY")
        self.base_url = config.get("OPENAI_BASE_URL")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(self, user_query: str) -> dict:
        """
        处理用户提问，返回回答和参考上下文。
        """
        logger.info(f"Processing query: {user_query}")
        
        # 1. 意图识别与关键词提取
        parsed_intent = self.parser.parse(user_query)
        logger.info(f"Parsed intent: {parsed_intent}")
        
        # 2. 图谱检索
        context = self.retriever.retrieve(parsed_intent)
        logger.info(f"Retrieved context length: {len(context)}")
        
        # 3. 构建 Prompt 并生成回答
        system_prompt = """
        你是一名资深的保险与医养专家，服务于泰康保险集团。你的职责是利用提供的专业知识库（Context）来回答客户关于保险产品、疾病医疗和养老机构的问题。

        回答要求：
        1. **基于事实**：严格基于提供的 [Context] 信息回答。如果 Context 中没有相关信息，请诚实告知用户“知识库中暂未收录相关信息”，不要编造。
        2. **专业亲切**：语气要专业、温暖、值得信赖，体现泰康“尊重生命、关爱生命”的价值观。
        3. **结构清晰**：如果涉及多个推荐（如药品、保险、养老院），请使用列表形式展示。
        4. **综合建议**：在回答保险问题时，可适当结合医疗或养老建议（如提到高血压险时，可顺带提醒注意饮食和监测血压）。
        """

        user_prompt = f"""
        [Context - 参考知识库]
        {context}

        [User Question - 用户问题]
        {user_query}

        请根据参考知识库回答用户问题：
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat", # 根据实际模型调整
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3, # 降低温度以保证回答基于事实
                max_tokens=1000
            )
            answer = response.choices[0].message.content
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

if __name__ == "__main__":
    # 测试代码
    engine = RAGEngine()
    try:
        test_q = "我今年70岁了，有高血压，想找个北京的养老院，顺便问问有什么保险能买？"
        result = engine.chat(test_q)
        print("\n=== 用户问题 ===")
        print(test_q)
        print("\n=== 参考知识 (Context) ===")
        print(result["context"])
        print("\n=== AI 回答 ===")
        print(result["answer"])
    finally:
        engine.close()
