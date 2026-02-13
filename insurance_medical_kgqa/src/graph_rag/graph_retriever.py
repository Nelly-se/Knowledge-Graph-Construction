from neo4j import GraphDatabase
from src.utils.config_loader import config
from src.utils.logger import logger

class GraphRetriever:
    def __init__(self):
        self.uri = config.get("neo4j", {}).get("uri", "bolt://localhost:7687")
        self.username = config.get("neo4j", {}).get("username", "neo4j")
        self.password = config.get("neo4j", {}).get("password", "password")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def retrieve(self, parsed_query: dict) -> str:
        """
        根据解析后的查询意图和关键词，在 Neo4j 中检索相关子图，
        并返回格式化的 Context 文本。
        """
        if not self.driver:
            return "Error: Database connection unavailable."

        context_parts = []
        intent = parsed_query.get("intent", "general_qa")
        diseases = parsed_query.get("disease", [])
        drugs = parsed_query.get("drug", [])
        age = parsed_query.get("age")
        city = parsed_query.get("city")
        
        with self.driver.session() as session:
            
            # 1. 疾病相关检索 (并发症、药品、保险)
            if diseases:
                for disease_name in diseases:
                    # 检索疾病基本信息、并发症、药品
                    cypher_disease = """
                    MATCH (d:Disease {name: $name})
                    OPTIONAL MATCH (d)-[:HAS_COMPLICATION]->(c:Disease)
                    OPTIONAL MATCH (d)-[:TREATED_BY]->(m:Drug)
                    OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
                    RETURN d, collect(DISTINCT c.name) as complications, 
                           collect(DISTINCT m.name) as drugs,
                           collect(DISTINCT s.name) as symptoms
                    """
                    result = session.run(cypher_disease, name=disease_name).single()
                    
                    if result:
                        d_node = result['d']
                        complications = result['complications']
                        drug_list = result['drugs']
                        symptom_list = result['symptoms']
                        
                        info = f"【疾病信息】{disease_name}:\n"
                        if d_node.get('intro'):
                            info += f"  - 简介: {d_node.get('intro')}\n"
                        if d_node.get('treat_detail'):
                            info += f"  - 治疗: {d_node.get('treat_detail')}\n"
                        if symptom_list:
                            info += f"  - 症状: {', '.join(symptom_list[:5])}\n"
                        if complications:
                            info += f"  - 并发症: {', '.join(complications[:5])}\n"
                        if drug_list:
                            info += f"  - 常用药物: {', '.join(drug_list[:5])}\n"
                        context_parts.append(info)

                    # 检索覆盖该疾病的保险
                    cypher_insurance = """
                    MATCH (i:Insurance)-[:COVERS_DISEASE]->(d:Disease {name: $name})
                    RETURN i.name as ins_name, i.description as desc, i.age_limit as age_limit
                    """
                    ins_results = session.run(cypher_insurance, name=disease_name)
                    ins_list = [f"{r['ins_name']} (年龄限制: {r['age_limit']})" for r in ins_results]
                    
                    if ins_list:
                        context_parts.append(f"【推荐保险】针对 {disease_name} 的相关保险产品: {', '.join(ins_list)}")

            # 2. 年龄相关保险检索 (如果有关联到 Population 或直接在 Insurance 属性中筛选)
            if age:
                # 简单逻辑：查找明确关联到“老年人”且包含该年龄段描述的保险
                # 这里假设只要关联了 '老年人' Population 且用户年龄 >= 60 就推荐
                if age >= 60:
                    cypher_age = """
                    MATCH (i:Insurance)-[:TARGETS_POPULATION]->(p:Population {name: '老年人'})
                    RETURN i.name as ins_name, i.age_limit as age_limit, i.description as desc
                    LIMIT 5
                    """
                    age_results = session.run(cypher_age)
                    rec_ins = []
                    for r in age_results:
                        rec_ins.append(f"{r['ins_name']} ({r['age_limit']})")
                    
                    if rec_ins:
                        context_parts.append(f"【适老保险】适合 {age} 岁人群的保险产品: {', '.join(rec_ins)}")

            # 3. 养老院检索
            if intent == "nursing_home_search" or city:
                params = {}
                query_parts = ["MATCH (n:NursingHome)"]
                where_clauses = []
                
                if city:
                    where_clauses.append("n.city CONTAINS $city")
                    params['city'] = city
                
                # 如果有价格限制可以在这里加 (需要 query_understanding 解析出 price_max)
                # where_clauses.append("toInteger(n.price) <= $price")
                
                if where_clauses:
                    query_parts.append("WHERE " + " AND ".join(where_clauses))
                
                query_parts.append("RETURN n.name as name, n.city as city, n.price as price, n.address as address LIMIT 5")
                
                nh_query = "\n".join(query_parts)
                nh_results = session.run(nh_query, **params)
                
                nh_list = []
                for r in nh_results:
                    nh_list.append(f"{r['name']} (城市: {r['city']}, 价格: {r['price']}, 地址: {r['address']})")
                
                if nh_list:
                    context_parts.append(f"【养老机构】推荐结果:\n  - " + "\n  - ".join(nh_list))

        if not context_parts:
            return "未在知识图谱中找到相关信息。"
        
        return "\n".join(context_parts)

if __name__ == "__main__":
    # 测试代码
    retriever = GraphRetriever()
    
    # 模拟 QueryParser 的输出
    mock_query = {
        "disease": ["高血压"],
        "age": 70,
        "intent": "insurance_query"
    }
    
    context = retriever.retrieve(mock_query)
    print(context)
    
    retriever.close()
