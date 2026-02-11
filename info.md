# 保险+医养知识图谱问答系统项目框架

## 项目概述
构建一个基于GraphRAG的跨领域知识图谱问答系统，整合保险、医疗、养老三大领域知识。

## 技术栈选择
- **知识图谱**: Neo4j + Py2neo
- **大模型**: Qwen-1.8B-Chat (本地部署) 或 阿里云百炼API
- **后端框架**: FastAPI
- **前端界面**: Streamlit (快速原型)
- **实体识别**: HanLP/BERT-NER
- **数据处理**: Pandas + SpaCy

## 项目目录结构

insurance_medical_kgqa/
├── data/                           # 数据目录
│   ├── raw/                       # 原始数据
│   ├── processed/                 # 处理后的数据
│   └── knowledge_base/            # 知识库文件
├── src/                           # 源代码
│   ├── kg_construction/           # 知识图谱构建模块
│   │   ├── __init__.py
│   │   ├── data_collection.py     # 数据收集
│   │   ├── ontology_design.py     # 本体设计
│   │   ├── entity_extraction.py   # 实体抽取
│   │   └── neo4j_loader.py        # Neo4j数据加载
│   ├── graph_rag/                 # GraphRAG核心引擎
│   │   ├── __init__.py
│   │   ├── query_understanding.py  # 查询理解
│   │   ├── graph_retrieval.py     # 图谱检索
│   │   ├── prompt_engineering.py  # Prompt工程
│   │   └── llm_integration.py     # 大模型集成
│   ├── api/                       # API接口
│   │   ├── __init__.py
│   │   └── main.py                # FastAPI主应用
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── config.py              # 配置文件
│       └── logger.py              # 日志配置
├── frontend/                      # 前端界面
│   ├── streamlit_app.py           # Streamlit应用
│   └── static/                    # 静态资源
├── tests/                         # 测试用例
├── docs/                          # 文档
├── requirements.txt               # 依赖包
├── config.yaml                    # 配置文件
└── README.md                      # 项目说明


## 核心模块实现要点

### 1. 知识图谱构建模块
python
kg_construction/ontology_design.py

class OntologyDesign:
    """本体设计类"""
    ENTITY_TYPES = {
        'Disease': ['name', 'code', 'category'],
        'Drug': ['name', 'ingredient', 'indication'],
        'InsuranceProduct': ['name', 'company', 'coverage'],
        'ElderlyService': ['name', 'type', 'location']
    }
    
    RELATIONSHIPS = [
        ('Disease', 'TREATED_BY', 'Drug'),
        ('InsuranceProduct', 'COVERS', 'Disease'),
        ('InsuranceProduct', 'HAS_AGE_LIMIT', 'AgeCondition')
    ]


### 2. GraphRAG引擎
python
graph_rag/graph_retrieval.py

class GraphRetriever:
    def retrieve_subgraph(self, entities, hops=2):
        """检索相关子图"""
        cypher_query = """
        MATCH (start) WHERE start.name IN $entities
        WITH start
        MATCH path = (start)-[*1..2]-(related)
        RETURN nodes(path) as nodes, relationships(path) as rels
        """
        # 执行Cypher查询...


### 3. Prompt工程模板
python
graph_rag/prompt_engineering.py

PROMPT_TEMPLATE = """
基于以下知识图谱信息，回答用户问题：

知识图谱信息：
{graph_context}

用户问题：{question}

请生成准确、专业的回答，并注明信息来源。
回答格式：
• 直接答案

• 依据：[相关三元组]

"""


## 配置文件示例
yaml
config.yaml

neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"

llm:
  model_type: "local"  # local 或 api
  local_model_path: "./models/Qwen-1.8B-Chat"
  api_key: "your_api_key"

data_sources:
  medical:
    ◦ "data/raw/icd_codes.csv"

    ◦ "data/raw/drugbank.json"

  insurance:
    ◦ "data/raw/insurance_products.csv"


## 部署步骤

1. **环境准备**
bash
conda create -n kgqa python=3.9
conda activate kgqa
pip install -r requirements.txt


2. **数据导入**
bash
python src/kg_construction/data_collection.py
python src/kg_construction/neo4j_loader.py


3. **启动服务**
bash
启动API服务

uvicorn src.api.main:app --reload

启动前端界面

streamlit run frontend/streamlit_app.py


## 关键依赖包
txt
requirements.txt

fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.0
py2neo==2021.2.3
pandas==2.0.3
hanlp==2.1.0
transformers==4.35.0
torch==2.1.0
openai==0.28.0
spacy==3.7.2


这个框架提供了完整的项目结构，便于在Cursor中逐步实现各个模块功能。