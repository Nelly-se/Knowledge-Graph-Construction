
import os
from neo4j import GraphDatabase
from src.utils.config_loader import config
from src.utils.logger import logger

class GraphRetriever:
    def __init__(self):
        self.uri = config.get("neo4j", {}).get("uri", "bolt://localhost:7687")
        self.username = config.get("neo4j", {}).get("username", "neo4j")
        self.password = config.get("neo4j", {}).get("password", "password")or os.getenv("NEO4J_PASSWORD")
        
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
        
        # === 修改点 1: 获取解析出的城市和价格上限 ===
        city = parsed_query.get("city")
        price_max = parsed_query.get("price_max") 
        
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

            # 2. 年龄相关保险检索
            if age:
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

# ... (保留上面的疾病和年龄检索代码) ...

            # ==========================================
            # === 修改点：增强版保险精准检索逻辑 ===
            # ==========================================
            if intent == "insurance_query":
                # 1. 动态确定要搜索的关键词
                # 默认搜所有，但如果用户提到了特定险种，就只搜那个险种
                target_category = "保险" # 默认宽泛搜索
                search_condition = ""
                
                # 简单粗暴的关键词匹配逻辑
                # 注意：这里需要确保 parsed_query 传递了原始问题 text，或者我们在 retrieve 里自己加参数
                # 假设 parsed_query 里没有 raw_question，我们这里用 intent 结合 disease 推断，或者硬编码几个分类
                
                # 更稳妥的方式：直接在 Cypher 里用 OR 匹配多个常见分类，或者让 LLM 提取出 insurance_type
                
                # 这里我们演示一种“混合过滤”写法：
                cypher_general_ins = """
                MATCH (i:Insurance)
                WHERE 1=1 
                """
                
                # 如果用户问的是“重疾”
                # 注意：这里我们假设 parsed_query 应该包含用户原始 query 里的关键词，
                # 但为了简单，我们直接在 Cypher 里做更聪明的匹配。
                
                # 真正的解决方案：根据意图过滤。
                # 由于你的 QueryParser 可能比较简单，我们这里用一种“广撒网但分类返回”的策略。
                
                cypher_general_ins = """
                MATCH (i:Insurance)
                // 只有当产品名称或分类包含‘重疾’、‘医疗’、‘意外’、‘护理’时才返回，避免返回无关的
                WHERE i.name CONTAINS '重疾' OR i.name CONTAINS '医疗' OR i.name CONTAINS '护理' OR i.name CONTAINS '防癌'
                RETURN i.name as name, 
                       i.age_limit as age_limit, 
                       i.description as desc,
                       i.category as category,
                       i.price as price
                ORDER BY rand()  // <--- 【新增】每次随机打乱顺序
                LIMIT 20
                """
                
                gen_results = session.run(cypher_general_ins)
                
                ins_data = []
                for r in gen_results:
                    ins_data.append({
                        "name": r['name'],
                        "category": r.get('category', '未知'), # 数据库里可能叫 '险种分类'，请核对属性名
                        "age_limit": r['age_limit'],
                        "desc": r['desc']
                    })

                # --- Python 层的二次过滤 (这是解决你问题的关键) ---
                # 既然 Cypher 处理字符串比较弱，我们在 Python 里帮它一把
                
                filtered_ins_list = []
                user_question_keywords = str(parsed_query).replace("'", "").replace('"', "") # 简易获取上下文里的字
                
                # 简单的分类器
                is_looking_for_critical = "重疾" in str(parsed_query) or "重大疾病" in str(parsed_query)
                is_looking_for_medical = "医疗" in str(parsed_query)
                
                for item in ins_data:
                    # 1. 类型过滤：如果用户明确问重疾，就不要给医疗
                    if is_looking_for_critical and "医疗" in item['name'] and "重疾" not in item['name']:
                        continue
                    if is_looking_for_medical and "重疾" in item['name']:
                        continue
                        
                    # 2. 格式化
                    item_str = f"【产品】{item['name']}\n   - 险种: {item['category']}\n   - 投保年龄: {item['age_limit']}\n   - 描述: {item['desc'][:50]}..."
                    filtered_ins_list.append(item_str)
                
                if filtered_ins_list:
                    # 提示词很重要：告诉 LLM 我给你的是一大堆，你要自己挑
                    context_parts.append(f"【保险产品库】(注意：请严格根据用户的年龄 {age} 岁和需求筛选以下产品，不要推荐年龄不符的产品):\n" + "\n".join(filtered_ins_list))
            # === 新增逻辑：3. 通用保险/关键词检索 (关键修改) ===
            # ==========================================
            # 如果意图是查保险，不仅查关联疾病的，还要把所有相关的险种捞出来让 LLM 筛选
            # if intent == "insurance_query":
            #     # 提取关键词，比如用户问“医疗险”，我们就查 name 包含“医疗”的产品
            #     # 这里做一个简单的规则：如果问题包含“医疗”，就搜“医疗”；包含“重疾”，搜“重疾”
            #     keywords = []
            #     # 注意：这里需要根据你的实际数据情况调整关键词
            #     # 假设你的产品名称里包含 "医疗", "重疾", "护理" 等词
            #     base_query_keywords = ["医疗", "重疾", "护理", "意外", "寿险"]
                
            #     # 简单的关键词匹配逻辑（也可以依赖 QueryParser 解析出的关键词）
            #     # 这里为了演示，我们直接查所有保险，按相关性排序
                
            #     cypher_general_ins = """
            #     MATCH (i:Insurance)
            #     WHERE i.name CONTAINS '医疗' OR i.category CONTAINS '医疗'  // 扩大搜索范围
            #     RETURN i.name as name, 
            #            i.age_limit as age_limit, 
            #            i.description as desc,
            #            i.category as category
            #     LIMIT 10
            #     """
                
            #     # 如果用户明确问了“重疾”，就改查重疾
            #     # 实际项目中，这里应该用 parsed_query.get('keywords')
                
            #     gen_results = session.run(cypher_general_ins)
                
            #     gen_ins_list = []
            #     for r in gen_results:
            #         # 格式化成一段文本，包含最重要的“年龄限制”
            #         item_str = f"【产品】{r['name']}\n   - 类型: {r['category']}\n   - 承保年龄: {r['age_limit']}\n   - 描述: {r['desc']}"
            #         gen_ins_list.append(item_str)
                
            #     if gen_ins_list:
            #         context_parts.append(f"【热门医疗保险列表】(请根据用户的年龄 {age} 岁自行筛选合适的):\n" + "\n".join(gen_ins_list))
            
            
            # === 修改点 2: 修复养老院检索逻辑 ===
            # 只要意图是找养老院，或者查询中包含了城市/价格，就触发检索
            if intent == "nursing_home_search" or city or price_max:
                params = {}
                # 基础查询
                query_parts = ["MATCH (n:NursingHome)"]
                where_clauses = []
                
                # 逻辑修复：如果在找城市，去 'address' 或 'name' 里找，而不是不存在的 'city' 属性
                if city:
                    where_clauses.append("(n.address CONTAINS $city OR n.name CONTAINS $city)")
                    params['city'] = city
                
                # 逻辑修复：启用价格过滤，注意数据库里的 price 是字符串，需要转数字
                if price_max:
                    where_clauses.append("toInteger(n.price) <= $price_max")
                    params['price_max'] = price_max
                
                if where_clauses:
                    query_parts.append("WHERE " + " AND ".join(where_clauses))
                
                # 逻辑修复：RETURN 中删除了 n.city，改用 address
                query_parts.append("""
                    RETURN n.name as name, 
                           n.price as price, 
                           n.address as address, 
                           n.services as services, 
                           n.beds as beds, 
                           n.nature as nature 
                        LIMIT 5
                """)                
                nh_query = "\n".join(query_parts)
                logger.info(f"Executing Cypher: {nh_query} | Params: {params}") # 添加日志方便调试
                
                nh_results = session.run(nh_query, **params)
                
                nh_list = []
                for r in nh_results:
                    # 4. 【关键修改】构建详细的信息卡片，而不是简单的一句话
                    detail = f"【{r['name']}】"
                    detail += f"\n  - 价格: {r['price']}元/月"
                    detail += f"\n  - 地址: {r['address']}"
                    
                    # 使用 .get() 或检查 None，防止数据缺失时报错
                    if r['nature']:
                        detail += f"\n  - 性质: {r['nature']}"
                    if r['beds']:
                        detail += f"\n  - 床位: {r['beds']}"
                    if r['services']:
                        # 截取过长的服务描述，避免 Context 爆长
                        services = r['services'][:100] + "..." if len(str(r['services'])) > 100 else r['services']
                        detail += f"\n  - 特色服务: {services}"
                    
                    nh_list.append(detail)
                
                if nh_list:
                    # 将结构化的文本加入 context
                    context_str = f"【养老机构推荐】(筛选条件: 城市={city or '不限'}, 预算<{price_max or '不限'}):\n" + "\n".join(nh_list)
                    context_parts.append(context_str)
                else:
                    context_parts.append(f"【养老机构】未找到符合条件的养老院 (城市: {city}, 预算: {price_max})。")

        # === ！！！必须确保这下面有这两行代码！！！ ===
        if not context_parts:
            return "知识图谱检索完成，但在图谱中未发现与该特定实体或条件直接匹配的记录。"
        
        return "\n".join(context_parts)  # <--- 这行丢失会导致报错！

if __name__ == "__main__":
    # 测试代码
    retriever = GraphRetriever()
    
    # 模拟 QueryParser 的输出
    mock_query = {
        "city": "北京",
        "price_max": 5000,
        "intent": "nursing_home_search"
    }
    
    context = retriever.retrieve(mock_query)
    print(context)
    
    retriever.close()