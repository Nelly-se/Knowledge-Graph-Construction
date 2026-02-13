# 泰康医养知识图谱问答系统 (Insurance & Medical KGQA)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-green)](https://neo4j.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-teal)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31%2B-red)](https://streamlit.io/)

本项目旨在构建一个垂直领域的智能问答系统，整合**泰康保险产品**、**医疗疾病**、**药品**及**养老机构**等多源数据，利用**知识图谱 (Knowledge Graph)** 和 **大语言模型 (LLM)** 技术（GraphRAG），提供专业、精准的医养保险咨询服务。

---

## 🚀 项目亮点 (MVP 1.0)

*   **多源异构数据融合**：整合了结构化数据（养老院 CSV）、半结构化数据（疾病/药品 JSON）和非结构化文本。
*   **知识图谱构建**：基于 Neo4j 构建包含 Disease, Drug, Symptom, NursingHome, Insurance 等核心实体的图谱。
*   **GraphRAG 引擎**：结合意图识别（Query Understanding）和图谱检索（Graph Retrieval），增强 LLM 的事实准确性。
*   **全栈交互体验**：提供 FastAPI 后端接口与 Streamlit 可视化对话界面，支持知识溯源展示。
*   **隐私安全**：敏感配置（API Key, DB Password）与代码分离，支持 `.env` 环境配置。

---

## 📂 目录结构

```plaintext
Knowledge-Graph-Construction/
├── DataCleaned/                # 清洗后的数据源
│   ├── 中老年疾病目录/
│   ├── 养老机构数据/
│   ├── 医保药品目录/
│   └── 医疗保险数据/
├── Documents/                  # 项目文档
├── insurance_medical_kgqa/     # 核心代码库
│   ├── frontend/               # 前端应用 (Streamlit)
│   │   └── app.py
│   ├── src/
│   │   ├── api/                # 后端接口 (FastAPI)
│   │   ├── graph_rag/          # RAG 核心引擎 (意图识别, 图检索)
│   │   ├── kg_construction/    # 图谱构建脚本
│   │   └── utils/              # 工具模块 (配置, 日志)
│   ├── config.yaml             # 公共配置文件
│   ├── .env.example            # 环境变量模板
│   └── .gitignore
└── README.md
```

---

## 🛠️ 安装与配置

### 1. 环境准备

确保已安装以下软件：
*   **Python 3.8+**
*   **Neo4j Desktop** (或服务器版)
*   **Git**

### 2. 安装依赖

```bash
cd insurance_medical_kgqa
pip install -r requirements.txt
# 如果暂无 requirements.txt，可手动安装核心依赖:
pip install fastapi uvicorn streamlit openai neo4j requests python-dotenv pyyaml pandas
```

### 3. 配置敏感信息

项目使用 `.env` 文件管理敏感信息。请复制模板并填入您的真实配置：

```bash
# 进入代码目录
cd insurance_medical_kgqa

# 复制模板
cp .env.example .env

# 编辑 .env 文件，填入您的 API Key 和 Neo4j 密码
# Windows 用户可用记事本打开 .env 编辑
```

`.env` 文件内容示例：
```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com
```

---

## 🏃‍♂️ 运行指南

### 1. 构建知识图谱 (数据导入)

确保 Neo4j 服务已启动，然后运行导入脚本：

```bash
cd insurance_medical_kgqa
python -m src.kg_construction.neo4j_loader
```
*该脚本会将 DataCleaned 目录下的数据批量导入 Neo4j 数据库。*

### 2. 启动服务

建议开启两个终端窗口，分别启动后端和前端。

**终端 1: 启动后端 API**
```bash
cd insurance_medical_kgqa
python -m src.api.main
```
*   API 文档地址: http://localhost:8000/docs

**终端 2: 启动前端界面**
```bash
cd insurance_medical_kgqa
streamlit run frontend/app.py
```
*   访问地址: http://localhost:8501

---

## 💡 使用示例

启动 Streamlit 界面后，您可以尝试询问：

*   **疾病查询**: "高血压有哪些并发症？"
*   **药品咨询**: "治疗糖尿病的常用药有哪些？"
*   **养老推荐**: "北京价格5000以下的养老院"
*   **保险建议**: "70岁老人适合买什么保险？"

系统将展示 AI 的回答，并在下方折叠框中显示**知识图谱溯源 (Reference)**，列出检索到的三元组信息。

---

## 🏗️ 技术栈详情

*   **图数据库**: Neo4j (Cypher Query Language)
*   **后端框架**: FastAPI (Python)
*   **前端框架**: Streamlit
*   **LLM 集成**: OpenAI SDK (适配 DeepSeek / GPT)
*   **配置管理**: Python-dotenv + PyYAML

---

## 📝 待办事项 (TODO)

- [ ] 增加更多种类的保险产品数据
- [ ] 优化多轮对话的上下文记忆
- [ ] 引入向量检索 (Vector Search) 增强非结构化文本的召回
- [ ] 部署至 Docker 容器

---

**Author**: 刘畅
**Date**: 2026-02
