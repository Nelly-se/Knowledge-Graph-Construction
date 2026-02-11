# FastAPI 主应用：问答等 API 路由
from typing import Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.utils.config import load_config, get_neo4j_config, get_llm_config
from src.utils.logger import get_logger
from src.kg_construction.neo4j_loader import Neo4jLoader
from src.graph_rag.query_understanding import QueryUnderstanding
from src.graph_rag.graph_retrieval import GraphRetriever
from src.graph_rag.prompt_engineering import build_qa_prompt, get_system_prompt
from src.graph_rag.llm_integration import LLMIntegration

logger = get_logger(__name__)

# ---------- 请求/响应模型 ----------
class QARequest(BaseModel):
    """问答请求体。"""
    question: str = Field(..., description="用户问题")
    max_hops: Optional[int] = Field(2, description="图谱检索跳数")
    temperature: Optional[float] = Field(0.7, description="LLM 温度")


class QAResponse(BaseModel):
    """问答响应体。"""
    answer: str = Field(..., description="生成答案")
    sources: Optional[list] = Field(None, description="依据的三元组或来源")
    graph_context: Optional[str] = Field(None, description="检索到的图谱摘要（调试用）")


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str = "ok"
    neo4j: Optional[bool] = None
    llm: Optional[bool] = None


# ---------- 全局依赖（启动时初始化） ----------
_neo4j_loader: Optional[Neo4jLoader] = None
_graph_retriever: Optional[GraphRetriever] = None
_query_understanding: Optional[QueryUnderstanding] = None
_llm: Optional[LLMIntegration] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时加载配置并初始化组件。"""
    global _neo4j_loader, _graph_retriever, _query_understanding, _llm
    try:
        config = load_config()
        # Neo4j
        neo4j_cfg = get_neo4j_config(config)
        _neo4j_loader = Neo4jLoader(
            uri=neo4j_cfg.get("uri", "bolt://localhost:7687"),
            username=neo4j_cfg.get("username", "neo4j"),
            password=neo4j_cfg.get("password", "password"),
        )
        _graph_retriever = GraphRetriever(_neo4j_loader, max_hops=2)
        _query_understanding = QueryUnderstanding()
        # LLM
        llm_cfg = get_llm_config(config)
        _llm = LLMIntegration(
            model_type=llm_cfg.get("model_type", "local"),
            model_path=llm_cfg.get("local_model_path"),
            api_key=llm_cfg.get("api_key"),
            api_base=llm_cfg.get("api_base"),
            model_name=llm_cfg.get("model_name"),
        )
        logger.info("API 依赖初始化完成")
    except Exception as e:
        logger.warning("部分依赖初始化失败，/qa 可能不可用: %s", e)
    yield
    if _neo4j_loader is not None:
        _neo4j_loader.close()
        logger.info("Neo4j 连接已关闭")


app = FastAPI(
    title="保险+医养知识图谱问答 API",
    description="基于 GraphRAG 的跨领域知识图谱问答",
    version="0.1.0",
    lifespan=lifespan,
)


def get_graph_retriever() -> GraphRetriever:
    """依赖：获取 GraphRetriever。"""
    if _graph_retriever is None:
        raise HTTPException(status_code=503, detail="图谱检索未初始化")
    return _graph_retriever


def get_llm() -> LLMIntegration:
    """依赖：获取 LLM。"""
    if _llm is None:
        raise HTTPException(status_code=503, detail="LLM 未初始化")
    return _llm


def _check_neo4j() -> bool:
    """检测 Neo4j 是否可用。"""
    if _neo4j_loader is None:
        return False
    try:
        _neo4j_loader.run_cypher("RETURN 1 AS n")
        return True
    except Exception:
        return False


def _check_llm() -> bool:
    """检测 LLM 是否可用（仅检查是否已配置 api 且 key 有效）。"""
    if _llm is None:
        return False
    return _llm.model_type == "api" and bool(_llm.api_key and _llm.api_key != "your_api_key")


# ---------- 路由 ----------
@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """健康检查。"""
    return HealthResponse(
        status="ok",
        neo4j=_check_neo4j(),
        llm=_check_llm(),
    )


@app.post("/qa", response_model=QAResponse)
def question_answer(req: QARequest) -> QAResponse:
    """问答：查询理解 -> 图谱检索 -> Prompt 组装 -> LLM 生成。"""
    retriever = get_graph_retriever()
    llm = get_llm()
    qu = _query_understanding
    if qu is None:
        raise HTTPException(status_code=503, detail="查询理解未初始化")

    intent = qu.parse(req.question)
    entities = intent.entities[:10]  # 限制实体数量
    hops = req.max_hops if req.max_hops is not None else 2

    subgraph = retriever.retrieve_subgraph(entities, hops=hops, limit=50)
    graph_context = retriever.subgraph_to_text(subgraph)

    prompt = build_qa_prompt(graph_context=graph_context, question=req.question)
    system_prompt = get_system_prompt()
    answer = llm.generate(
        prompt,
        system_prompt=system_prompt,
        temperature=req.temperature or 0.7,
        max_tokens=1024,
    )

    sources = [list(t) for t in subgraph.triples[:15]] if subgraph.triples else None
    return QAResponse(
        answer=answer,
        sources=sources,
        graph_context=graph_context if not graph_context.startswith("（未检索") else None,
    )


@app.get("/")
def root() -> dict:
    """根路径说明。"""
    return {
        "service": "保险+医养知识图谱问答 API",
        "docs": "/docs",
        "qa": "POST /qa",
        "health": "GET /health",
    }
