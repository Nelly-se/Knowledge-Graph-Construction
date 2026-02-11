# Streamlit 前端：问答界面，调用后端 API
"""
运行方式（在项目根目录）：
    streamlit run frontend/streamlit_app.py
"""
import streamlit as st
from typing import Optional

# 后端 API 基础 URL（可通过环境变量或侧边栏配置）
API_BASE = "http://localhost:8000"


def call_qa_api(question: str, max_hops: int = 2, temperature: float = 0.7) -> Optional[dict]:
    """
    调用后端 POST /qa 接口。
    Args:
        question: 用户问题。
        max_hops: 图谱检索跳数。
        temperature: LLM 温度。
    Returns:
        解析后的 JSON 或 None（请求失败时）。
    """
    # TODO: requests.post(f"{API_BASE}/qa", json={...})
    raise NotImplementedError


def render_sidebar() -> None:
    """侧边栏：API 地址、参数等。"""
    st.sidebar.title("设置")
    # TODO: st.sidebar.text_input("API 地址", value=API_BASE)
    # TODO: max_hops, temperature 等
    pass


def render_main() -> None:
    """主区域：问题输入、发送、答案展示。"""
    st.title("保险+医养知识图谱问答")
    st.caption("基于 GraphRAG 的跨领域问答")

    question = st.text_area("请输入您的问题", height=100, placeholder="例如：高血压有哪些保险产品可以覆盖？")
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.button("提交")
    # TODO: 与 col2 放「清空」等

    if submitted and question.strip():
        with st.spinner("正在检索图谱并生成回答..."):
            # result = call_qa_api(question.strip())
            # if result: st.write(result.get("answer")); st.json(result.get("sources"))
            st.info("请先实现 call_qa_api 并启动后端 API。")
    elif submitted:
        st.warning("请输入问题内容。")


def main() -> None:
    """应用入口。"""
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
