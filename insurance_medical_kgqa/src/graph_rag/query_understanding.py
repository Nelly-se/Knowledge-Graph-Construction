# 查询理解：用户问句解析与意图/实体识别
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryIntent:
    """查询意图与抽取结果。"""
    raw_question: str
    intent: str
    entities: List[str]
    keywords: List[str]


# 简单意图关键词映射（可后续替换为分类模型）
INTENT_KEYWORDS = {
    "insurance_coverage": ["保险", "覆盖", "保什么", "赔", "理赔", "产品"],
    "drug_query": ["药", "药物", "治疗", "服用", "疗效"],
    "elderly_service": ["养老", "护理", "照护", "老人", "康养"],
    "disease_query": ["病", "疾病", "症状", "诊断", "患病"],
}


class QueryUnderstanding:
    """查询理解：从用户问句解析意图与实体，供图谱检索使用。"""

    def __init__(self, ner_model: Optional[Any] = None, intent_labels: Optional[List[str]] = None):
        self.ner_model = ner_model
        self.intent_labels = intent_labels or list(INTENT_KEYWORDS.keys())

    def parse(self, question: str) -> QueryIntent:
        """解析用户问句，得到意图与实体。"""
        question = (question or "").strip()
        # 简单关键词意图
        intent = "general"
        for label, keywords in INTENT_KEYWORDS.items():
            if any(k in question for k in keywords):
                intent = label
                break
        # 简单实体抽取：2~10 个连续中文字符或英文词，过滤纯数字与停用词
        stop = {"什么", "哪些", "如何", "怎么", "可以", "有没有", "是否", "的", "了", "吗", "呢"}
        words = re.findall(r"[\u4e00-\u9fa5]{2,10}|[A-Za-z0-9]+", question)
        entities = [w for w in words if w not in stop and not w.isdigit()]
        # 若没有明显实体，将整句关键词作为检索词（便于全文/名称匹配）
        if not entities:
            entities = [question[:20]] if question else []
        keywords = list(entities[:5])
        return QueryIntent(raw_question=question, intent=intent, entities=entities, keywords=keywords)

    def get_entities(self, question: str) -> List[str]:
        return self.parse(question).entities

    def get_intent(self, question: str) -> str:
        return self.parse(question).intent
