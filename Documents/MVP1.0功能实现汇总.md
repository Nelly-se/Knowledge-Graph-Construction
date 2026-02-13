# 泰康医养知识图谱问答系统 (MVP 1.0) 功能实现汇总

## 1. 项目概述
本项目旨在构建一个基于知识图谱 (Neo4j) 和大语言模型 (LLM) 的垂直领域问答系统，专注于泰康保险、医疗疾病、药品及养老机构等领域的知识整合与智能问答。

## 2. 已实现功能模块

### 2.1 基础设施 (Infrastructure)
- **配置管理 (`src/utils/config_loader.py`)**: 
  - 实现了基于 YAML 的全局配置加载。
  - 支持自动定位项目根目录，避免硬编码绝对路径。
- **日志系统 (`src/utils/logger.py`)**: 
  - 统一的日志记录格式，支持控制台和文件输出，便于调试和监控。

### 2.2 知识图谱构建 (KG Construction)
- **数据加载器 (`src/kg_construction/neo4j_loader.py`)**:
  - **数据源解析**: 支持 JSON (疾病、药品、保险) 和 CSV (养老机构) 格式数据的清洗与加载。
  - **节点设计**: 
    - `Disease` (疾病): 包含名称、ICD编码、治疗详情等。
    - `Drug` (药品): 包含名称、规格等。
    - `Symptom` (症状): 从疾病关联中提取。
    - `NursingHome` (养老机构): 包含名称、城市、价格、地址等。
    - `Insurance` (保险): 包含名称、适用人群、年龄限制等。
    - `Department` (科室): 疾病所属科室。
  - **关系构建**:
    - `(Disease)-[:HAS_SYMPTOM]->(Symptom)`
    - `(Disease)-[:TREATED_BY]->(Drug)`
    - `(Disease)-[:BELONGS_TO_DEPT]->(Department)`
    - `(Disease)-[:HAS_COMPLICATION]->(Disease)`
    - `(Insurance)-[:COVERS_DISEASE]->(Disease)`
    - `(Insurance)-[:TARGETS_POPULATION]->(Population)`
  - **批量导入**: 使用 Neo4j `UNWIND` 语法优化写入性能。
  - **数据约束**: 自动创建唯一性约束，防止重复数据。

### 2.3 图谱检索增强生成 (GraphRAG)
- **意图识别 (`src/graph_rag/query_understanding.py`)**:
  - 利用 LLM (DeepSeek) 将自然语言问题解析为结构化意图 (Intent) 和实体 (Entities)。
  - 示例: "70岁高血压能买什么险" -> `{"age": 70, "disease": ["高血压"], "intent": "insurance_query"}`。
- **图谱检索 (`src/graph_rag/graph_retriever.py`)**:
  - 根据解析的意图动态构建 Cypher 查询语句。
  - 支持多跳查询 (如: 疾病 -> 并发症 -> 药品)。
  - 支持条件过滤 (如: 养老院价格、城市筛选)。
  - 输出结构化的 Context 文本供 LLM 参考。
- **RAG 引擎 (`src/graph_rag/rag_engine.py`)**:
  - 整合意图识别、图谱检索和 LLM 生成流程。
  - 设计了 "保险+医养专家" 的 System Prompt，确保回答专业、亲切且基于事实。

### 2.4 后端服务 (Backend API)
- **FastAPI 接口 (`src/api/main.py`)**:
  - 提供 `/chat` POST 接口，接收用户问题，返回 JSON 格式的回答及溯源信息。
  - 实现了应用生命周期管理，自动初始化和关闭数据库连接。

### 2.5 前端交互 (Frontend)
- **Streamlit 应用 (`frontend/app.py`)**:
  - **对话界面**: 类似 ChatGPT 的流式对话体验。
  - **知识溯源**: 展示 AI 回答所参考的图谱节点信息 (Reference)。
  - **数据概览**: 侧边栏实时展示图谱中各类节点的数量统计。

## 3. 技术栈
- **数据库**: Neo4j
- **后端**: Python, FastAPI
- **前端**: Streamlit
- **LLM**: DeepSeek (via OpenAI Client)
- **工具库**: Pandas, Neo4j Driver, PyYAML

## 4. 隐私与安全 (进行中)
- 正在进行敏感信息 (API Keys, 数据库密码) 的抽离与保护，确保代码可安全开源。
