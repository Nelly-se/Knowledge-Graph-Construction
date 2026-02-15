# 🏥 泰康医养知识图谱智能问答系统 (Insurance-Medical-KGQA) 

> **基于 GraphRAG 的跨领域垂直知识图谱问答系统** > 整合 **保险产品**、**疾病医疗**、**养老机构** 三大领域数据，利用 Neo4j 图数据库与大语言模型（LLM）实现精准的智能问答与推荐。

## 🌟 项目亮点

* **GraphRAG 架构**：结合知识图谱的结构化检索与大模型的语义理解，解决 LLM 在垂直领域的幻觉问题。
* **多源数据融合**：打通了“疾病-药品”、“疾病-保险”、“老人-养老院”的数据链路。
* **精准推荐算法**：基于用户画像（年龄、疾病历史）的保险与养老机构推荐算法（支持精准年龄校验）。
* **企业级安全规范**：采用 `.env` 环境变量管理敏感密钥，杜绝硬编码安全隐患。
* **现代化 UI 交互**：基于 Streamlit 构建的适老化、卡片式医疗专业前端界面。

---

## 🛠️ 技术栈

| 模块          | 技术选型                 | 说明                                      |
| :------------ | :----------------------- | :---------------------------------------- |
| **知识图谱**  | **Neo4j**                | 图数据存储与 Cypher 查询                  |
| **大模型**    | **Qwen (通义千问)**      | 通过阿里云百炼 API 调用 (OpenAI 兼容协议) |
| **后端框架**  | **FastAPI**              | 高性能异步 REST API                       |
| **前端界面**  | **Streamlit**            | 数据可视化与交互界面 (Custom CSS 优化)    |
| **驱动/工具** | `neo4j-driver`, `openai` | Python SDK                                |

---



## 📂 项目目录结构

```
insurance_medical_kgqa/
├── .env                  # [新增] 敏感环境变量（API Key, 数据库密码），切勿上传！
├── .gitignore            # Git 忽略规则配置
├── config.yaml           # [更新] 公共配置文件（模型名称、数据路径、服务地址）
├── requirements.txt      # Python 依赖列表
├── README.md             # 项目说明文档
│
├── DataCleaned/          # 清洗后的结构化数据
│   ├── Diseases/         # 疾病数据
│   ├── Drugs/            # 药品数据
│   ├── Insurance/        # 保险产品数据
│   └── NursingHomes/     # 养老院数据
│
├── frontend/             # 前端应用
│   └── streamlit_app.py  # Streamlit 启动入口（含 UI 优化逻辑）
│
└── src/                  # 核心源代码
    ├── api/              # API 接口层
    │   └── main.py       # FastAPI 启动入口
    │
    ├── graph_rag/        # RAG 核心引擎
    │   ├── graph_retriever.py    # 图谱检索器（含随机排序与精准过滤）
    │   ├── query_understanding.py # 意图识别模块
    │   ├── rag_engine.py         # 问答流程控制
    │   └── llm_integration.py    # [重构] LLM 统一调用接口（自动读取 .env）
    │
    ├── kg_construction/  # 图谱构建模块
    │   └── neo4j_loader.py       # 数据导入脚本
    │
    └── utils/            # 通用工具
        ├── config_loader.py      # 配置加载器
        └── logger.py             # 日志模块
```

------

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

推荐使用 Python 3.10 或 3.11 版本。

Bash

```
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安全配置 (至关重要！⚠️)

本项目不再将密钥明文写入 `config.yaml`。请在项目根目录下新建一个名为 `.env` 的文件，并填入你的私密信息：

**`.env` 文件内容示例：**

Ini, TOML

```
# Neo4j 数据库密码
NEO4J_PASSWORD=你的数据库密码

# 阿里云百炼 API Key
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **注意**：`.env` 文件已被加入 `.gitignore`，请确保不要将其上传到 GitHub。

### 3. 公共配置 (`config.yaml`)

`config.yaml` 仅用于配置非敏感信息，如模型名称、服务地址等。

YAML

```
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  # password: 由 .env 管理

llm:
  model_type: "api"
  api_base: "[https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)"
  model_name: "qwen-turbo"  # 可随时更改模型，如 qwen-max
  # api_key: 由 .env 管理
```

------

## 🏃‍♂️ 启动服务

本项目采用**前后端分离**架构，启动时需要打开 **3个** 独立的终端窗口。

### 第一步：启动 Neo4j 数据库

确保你的 Neo4j Desktop 或服务已开启。

Bash

```
neo4j console
```

### 第二步：启动后端 API (FastAPI)

在项目根目录下运行：

Bash

```
uvicorn src.api.main:app --reload
```

- 成功标志：看到 `Application startup complete`。
- API 文档地址：http://127.0.0.1:8000/docs

### 第三步：启动前端界面 (Streamlit)

在项目根目录下运行：

Bash

```
streamlit run frontend/streamlit_app.py
```

- 成功标志：浏览器自动打开 http://localhost:8501。

------

## 📝 使用指南

1. **问保险**：
   - *"70岁高血压老人推荐买什么保险？"*
   - 系统会自动校验年龄限制，并优先检索适合高龄人群的“防癌险”或“特药险”，避免推荐超龄产品。
2. **问养老**：
   - *"北京价格5000元以下的养老院有哪些？"*
3. **问医疗**：
   - *"糖尿病有哪些并发症？"*

------

## 🔧 常见问题 (Troubleshooting)

**Q1: 启动后端报错 `OPENAI_API_KEY not found` 或 `Auth Error`？**

- 检查项目根目录下是否有 `.env` 文件。
- 检查 `.env` 中的变量名是否为 `DASHSCOPE_API_KEY`。
- 确保 `llm_integration.py` 中已正确引入 `load_dotenv()`。

**Q2: 前端报错 `st.columns argument must be positive integer`？**

- 这是由于检索结果为空导致的渲染错误。最新版代码已修复此问题，请确保拉取了最新的 `streamlit_app.py`。

**Q3: 推荐的保险总是那几款？**

- 我们在 `graph_retriever.py` 中加入了 `ORDER BY rand()` 机制，每次检索会随机打乱同类产品，保证多样性。

------

## 👥 贡献者

- Project Owner:刘畅，Nelly-se

------

*Last Updated: 2026-02-15*