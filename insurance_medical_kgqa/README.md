# 保险+医养知识图谱问答系统

基于 GraphRAG 的跨领域知识图谱问答系统，整合保险、医疗、养老三大领域知识，支持自然语言提问并基于知识图谱与大模型生成回答。

---

## 一、项目框架

### 1.1 技术栈

| 层级     | 技术 |
|----------|------|
| 知识图谱 | Neo4j + Py2neo |
| 大模型   | 阿里云百炼 API（OpenAI 兼容）/ 本地 Qwen |
| 后端     | FastAPI |
| 前端     | Streamlit |
| 配置     | YAML（config.yaml） |

### 1.2 目录结构

```
insurance_medical_kgqa/
├── config.yaml              # 项目配置（Neo4j、LLM、数据源）
├── requirements.txt         # Python 依赖
├── README.md
│
├── data/                    # 数据目录
│   ├── raw/                 # 原始数据（CSV、JSON 等）
│   ├── processed/           # 处理后的数据
│   └── knowledge_base/      # 知识库文件
│
├── src/                     # 源代码
│   ├── kg_construction/     # 知识图谱构建
│   │   ├── data_collection.py   # 数据收集与加载
│   │   ├── ontology_design.py   # 本体设计（实体/关系 schema）
│   │   ├── entity_extraction.py # 实体与关系抽取
│   │   └── neo4j_loader.py      # Neo4j 连接与数据写入
│   │
│   ├── graph_rag/            # GraphRAG 问答引擎
│   │   ├── query_understanding.py  # 查询理解（意图、实体）
│   │   ├── graph_retrieval.py      # 子图检索
│   │   ├── prompt_engineering.py   # Prompt 模板与组装
│   │   └── llm_integration.py      # 大模型调用封装
│   │
│   ├── api/                  # 后端 API
│   │   └── main.py           # FastAPI 应用（/qa、/health）
│   │
│   └── utils/                # 工具
│       ├── config.py        # 配置加载
│       └── logger.py        # 日志
│
├── frontend/                 # 前端
│   ├── streamlit_app.py     # Streamlit 问答界面
│   └── static/               # 静态资源
│
├── tests/                    # 测试
└── docs/                     # 文档（含 module_interfaces.md）
```

### 1.3 数据流与调用链

- **构建阶段**：原始数据 → 数据收集 → 实体/关系抽取 → Neo4j 写入  
- **问答阶段**：用户问题 → 查询理解（实体/意图）→ 子图检索 → Prompt 组装 → LLM 生成 → 返回答案

---

## 二、配置说明

### 2.1 配置文件 `config.yaml`

项目根目录下的 `config.yaml` 为统一配置入口，需在**首次运行前**按实际环境修改。

```yaml
# Neo4j 图数据库（必配：用于图谱检索）
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"

# 大模型（问答必配：建议使用 api 模式）
llm:
  model_type: "api"           # "local" 本地模型 | "api" 百炼等 API
  local_model_path: "./models/Qwen-1.8B-Chat"   # model_type=local 时使用
  api_key: "your_api_key"     # model_type=api 时必填（如百炼 API Key）
  api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 可选，默认百炼兼容地址
  model_name: "qwen-turbo"    # API 模型名，可选

# 数据源路径（用于知识图谱构建与数据导入）
data_sources:
  medical:
    - "data/raw/icd_codes.csv"
    - "data/raw/drugbank.json"
  insurance:
    - "data/raw/insurance_products.csv"
```

### 2.2 配置项说明

| 配置项 | 说明 |
|--------|------|
| `neo4j.uri` | Neo4j Bolt 地址，本地一般为 `bolt://localhost:7687` |
| `neo4j.username` / `neo4j.password` | Neo4j 登录账号密码 |
| `llm.model_type` | `api`：使用百炼等 HTTP API；`local`：本地模型（需自行实现加载） |
| `llm.api_key` | 使用 API 时必填，在阿里云百炼控制台获取 |
| `data_sources` | 构建图谱时读取的原始数据路径，相对项目根目录 |

---

## 三、使用操作

### 3.1 环境准备

在项目根目录 `insurance_medical_kgqa` 下执行：

```bash
# 建议使用 Python 3.9+
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3.2 启动 Neo4j（可选但推荐）

- 安装并启动 Neo4j 社区版，默认端口 `7687`。  
- 若未启动 Neo4j，API 仍可运行，但 `/health` 中 `neo4j` 为 `false`，图谱检索无数据。

### 3.3 数据导入（构建知识图谱）

在实现好 `data_collection`、`entity_extraction`、`neo4j_loader` 后，可执行：

```bash
# 在项目根目录下
python -m src.kg_construction.data_collection   # 按需：收集/预处理数据
python -m src.kg_construction.neo4j_loader       # 按需：将三元组写入 Neo4j
```

具体脚本入口以各模块实现为准；未导入数据时，问答仍可调用，但检索子图可能为空。

### 3.4 启动后端 API

在项目根目录下执行：

```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

- API 文档（Swagger）：<http://127.0.0.1:8000/docs>  
- 健康检查：<http://127.0.0.1:8000/health>  
- 问答接口：`POST http://127.0.0.1:8000/qa`

### 3.5 启动前端界面

**先保持后端 API 已启动**，再新开终端：

```bash
# 仍在项目根目录
streamlit run frontend/streamlit_app.py
```

浏览器访问 Streamlit 提示的地址（通常为 <http://localhost:8501>），在界面中输入问题即可调用后端 `/qa` 进行问答。

### 3.6 直接调用问答 API

**请求示例：**

```bash
curl -X POST "http://127.0.0.1:8000/qa" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"高血压有哪些保险可以覆盖？\", \"max_hops\": 2}"
```

**请求体（JSON）：**

| 字段        | 类型   | 必填 | 说明           |
|-------------|--------|------|----------------|
| question    | string | 是   | 用户问题       |
| max_hops    | int    | 否   | 图谱检索跳数，默认 2 |
| temperature | float  | 否   | LLM 温度，默认 0.7 |

**响应示例：**

```json
{
  "answer": "根据知识图谱……",
  "sources": [["实体A", "关系", "实体B"], ...],
  "graph_context": "三元组：\n  (高血压)-[COVERS]->(某保险产品)"
}
```

---

## 四、常见问题

- **问答返回“请配置 LLM”**：在 `config.yaml` 中设置 `llm.model_type: "api"` 并填写有效的 `llm.api_key`。  
- **health 中 neo4j 为 false**：检查 Neo4j 是否已启动，以及 `config.yaml` 中 `neo4j` 的 uri/用户名密码是否正确。  
- **检索不到图谱信息**：确认已通过数据导入流程向 Neo4j 写入过三元组，且问句中包含与图谱中实体相关的关键词。

更多模块接口说明见 `docs/module_interfaces.md`，整体设计可参考项目根目录的 `info.md`。
