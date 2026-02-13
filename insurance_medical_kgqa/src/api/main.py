from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
import uvicorn
from contextlib import asynccontextmanager

from src.graph_rag.rag_engine import RAGEngine
from src.utils.logger import logger

# 定义请求模型
class ChatRequest(BaseModel):
    query: str

# 定义响应模型
class ChatResponse(BaseModel):
    answer: str
    context: str
    intent: Optional[dict] = None

# 全局 RAG 引擎实例
rag_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    global rag_engine
    logger.info("Initializing RAG Engine...")
    rag_engine = RAGEngine()
    yield
    # 关闭时清理
    logger.info("Closing RAG Engine...")
    if rag_engine:
        rag_engine.close()

app = FastAPI(title="Insurance & Medical KGQA API", lifespan=lifespan)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = rag_engine.chat(request.query)
        return ChatResponse(
            answer=result["answer"],
            context=result["context"],
            intent=result["intent"]
        )
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
