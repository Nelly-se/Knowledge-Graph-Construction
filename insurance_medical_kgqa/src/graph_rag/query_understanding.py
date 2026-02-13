import json
from openai import OpenAI
from src.utils.config_loader import config
from src.utils.logger import logger

class QueryParser:
    def __init__(self):
        self.api_key = config.get("OPENAI_API_KEY")
        self.base_url = config.get("OPENAI_BASE_URL")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in config. Query understanding may fail.")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def parse(self, user_query: str) -> dict:
        """
        调用 LLM 将用户问题解析为结构化关键词。
        """
        system_prompt = """
        你是一个医疗与保险领域的知识图谱助手。请提取用户问题中的关键实体和意图，并以 JSON 格式返回。
        
        支持提取的字段包括：
        - disease: 疾病名称（列表），如 ["高血压", "糖尿病"]
        - symptom: 症状（列表），如 ["头痛", "胸闷"]
        - drug: 药品名称（列表）
        - age: 年龄（数字），如 70
        - city: 城市名称（字符串），用于养老院查询
        - intent: 用户意图，可选值：
            - "treatment" (询问治疗/药品)
            - "insurance_query" (询问保险产品)
            - "nursing_home_search" (寻找养老院)
            - "complication_query" (询问并发症)
            - "general_qa" (其他)
            
        示例：
        用户输入："70岁高血压能买什么险"
        输出：{"age": 70, "disease": ["高血压"], "intent": "insurance_query"}
        
        用户输入："北京有哪些价格在5000以下的养老院"
        输出：{"city": "北京", "price_max": 5000, "intent": "nursing_home_search"}
        
        如果未找到相关信息，字段可省略或设为 null/空列表。仅返回 JSON 字符串，不要包含 Markdown 格式。
        """

        try:
            logger.info(f"Parsing query: {user_query}")
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # 假设使用 deepseek-chat，根据实际情况调整
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM Parse Result: {content}")
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error parsing query with LLM: {e}")
            # Fallback: 简单的关键词匹配（可选）
            return {"intent": "general_qa", "original_query": user_query}

if __name__ == "__main__":
    # 测试代码
    parser = QueryParser()
    test_query = "70岁高血压能买什么险"
    print(json.dumps(parser.parse(test_query), ensure_ascii=False, indent=2))
