import streamlit as st
import requests
import re

# ==========================================
# 1. 配置与全局样式 (Visual Design & CSS)
# ==========================================
st.set_page_config(
    page_title="泰康医养智能助手",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 品牌色定义
PRIMARY_COLOR = "#2E86DE"  # 医疗蓝 (信任/专业)
ACCENT_COLOR = "#00B894"   # 生命绿 (健康)
BG_COLOR = "#F4F7F6"       # 浅灰背景 (护眼)
CARD_BG = "#FFFFFF"        # 卡片白
TEXT_COLOR = "#2D3436"     # 深灰字 (高对比度)

# 注入自定义 CSS
st.markdown(f"""
<style>
    /* 全局背景与字体 */
    .stApp {{
        background-color: {BG_COLOR};
        font-family: "Microsoft YaHei", "Segoe UI", Roboto, sans-serif;
    }}
    
    /* 标题样式 */
    h1, h2, h3 {{
        color: {PRIMARY_COLOR} !important;
        font-weight: 600;
    }}
    
    /* 侧边栏优化 */
    [data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }}
    
    /* 聊天气泡/卡片通用样式 */
    .chat-card {{
        background-color: {CARD_BG};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); /* 轻微阴影 */
        border-left: 5px solid {PRIMARY_COLOR}; /* 左侧强调线 */
    }}
    
    /* 推荐产品卡片 (特殊强调) */
    .product-card {{
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(46, 134, 222, 0.1);
        transition: transform 0.2s;
    }}
    .product-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(46, 134, 222, 0.15);
    }}
    
    /* 关键数据高亮 (适老设计) */
    .highlight-data {{
        color: {ACCENT_COLOR};
        font-weight: bold;
        font-size: 1.1em;
    }}
    
    /* 按钮美化 */
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 25px;
        height: 50px;
        padding: 0 30px;
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 6px rgba(46, 134, 222, 0.3);
    }}
    .stButton>button:hover {{
        background-color: #2674c2;
    }}
    
    /* 调整正文字号 (适老) */
    p, li {{
        font-size: 16px !important;
        line-height: 1.6 !important;
        color: {TEXT_COLOR};
    }}
</style>
""", unsafe_allow_html=True)

# API 地址
API_URL = "http://127.0.0.1:8000/chat"

# ==========================================
# 2. 功能函数
# ==========================================

def get_graph_stats():
    """模拟图谱统计数据 (实际项目可调后端 API)"""
    return {
        "Disease": "403",
        "Drug": "3,827",
        "Insurance": "78",
        "NursingHome": "469",
        "Symptom": "2,000+"
    }

def format_product_card(text_segment):
    """
    尝试将一段文本渲染为漂亮的卡片。
    主要用于处理 '1. xxx保险' 这样的结构。
    """
    # 简单的正则提取标题，假设格式为 "1. 产品名" 或 "【产品名】"
    title_match = re.match(r"^\d+\.\s*(.*)|【(.*)】", text_segment.split('\n')[0])
    title = title_match.group(1) or title_match.group(2) if title_match else "推荐方案"
    
    # 提取剩余内容
    content = "\n".join(text_segment.split('\n')[1:])
    
    # --- 修复点：先在外面处理换行符，不要在 f-string 里写 \n ---
    content_html = content.replace('\n', '<br>')

    # 使用 HTML/CSS 渲染卡片
    st.markdown(f"""
    <div class="product-card">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 24px; margin-right: 10px;">🛡️</span>
            <h3 style="margin:0; color: #2E86DE;">{title}</h3>
        </div>
        <div style="color: #555; font-size: 16px;">
            {content_html} 
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_smart_answer(answer_text):
    """
    智能解析回答文本。
    如果检测到列表结构（推荐多个产品），尝试拆分卡片展示。
    否则展示标准文本卡片。
    """
    # 检查是否包含 "1. " 且 "2. " 这种列表结构，且是在推荐保险或养老院
    if ("1." in answer_text and "2." in answer_text) and ("保险" in answer_text or "养老院" in answer_text):
        st.markdown("### 为您甄选以下方案：")
        
        # 简单切分：按数字列表切分
        # 注意：这只是一个简易的切分逻辑，依赖 LLM 输出格式比较规范
        segments = re.split(r'(?=\n\d+\.)', answer_text)
        
        # 第一段通常是开场白
        if segments and not re.match(r'\d+\.', segments[0].strip()):
            st.markdown(f"<div style='margin-bottom:15px'>{segments[0]}</div>", unsafe_allow_html=True)
            segments = segments[1:]
            
        # 渲染产品卡片
        # === 修复点：确保 segments 不为空才创建列 ===
        if len(segments) > 0:
            # 动态计算列数，最多2列
            num_cols = min(len(segments), 2)
            cols = st.columns(num_cols)
            
            for i, seg in enumerate(segments):
                if seg.strip():
                    # 轮流在两列中渲染
                    with cols[i % num_cols]:
                        format_product_card(seg.strip())
    else:
        # --- 修复点：先在外面处理换行符 ---
        answer_html = answer_text.replace('\n', '<br>')

        # 普通回答，使用整体卡片
        st.markdown(f"""
        <div class="chat-card">
            {answer_html}
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. 界面布局
# ==========================================

# --- 侧边栏 ---
with st.sidebar:
    st.image("https://www.taikang.com/favicon.ico", width=60) 
    st.title("泰康医养 KGQA")
    st.markdown("---")
    
    st.markdown("### 📊 知识储备")
    stats = get_graph_stats()
    
    # 统计数据使用指标展示
    c1, c2 = st.columns(2)
    c1.metric("疾病库", stats["Disease"], delta_color="normal")
    c1.metric("保险产品", stats["Insurance"])
    c2.metric("药品库", stats["Drug"])
    c2.metric("合作养老院", stats["NursingHome"])
    
    st.markdown("---")
    st.markdown("### ⚙️ 偏好设置")
    temperature = st.slider("严谨度 (Temperature)", 0.0, 1.0, 0.3, help="数值越低，回答越保守严谨；数值越高，回答越发散。")
    
    st.info("💡 **提示**：我是基于知识图谱的专家助手，请尽量描述清楚您的年龄和健康状况，以便我为您推荐精准的保险或养老方案。")

# --- 主区域 ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("# 🏥")
with col_title:
    st.title("泰康保险医养智能助手")
    st.caption("基于 GraphRAG 技术 | 您的专属健康财富管家")

# 初始化历史记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            # 如果是历史消息，简化展示（或者也可以调用 smart_display）
            st.markdown(msg["content"]) 
            if "context" in msg and msg["context"]:
                with st.expander("📚 查看参考来源 (知识图谱溯源)"):
                    st.info(msg["context"])
        else:
            st.markdown(msg["content"])

# --- 输入区域 ---
prompt = st.chat_input("请描述您的情况，例如：70岁老人有高血压，推荐什么保险？")

if prompt:
    # 1. 展示用户提问
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 获取 AI 回答
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        with st.spinner("👩‍⚕️ 正在查阅知识库，为您分析最佳方案..."):
            try:
                # 调用后端 API
                payload = {"query": prompt}
                # 可以在这里把 temperature 传给后端（如果后端支持）
                
                response = requests.post(API_URL, json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "抱歉，我没有理解您的问题。")
                    context = data.get("context", "")
                    
                    # 使用智能卡片展示
                    display_smart_answer(answer)
                    
                    # 溯源信息
                    if context and len(context) > 10:
                        with st.expander("📚 知识图谱溯源 (Evidence)"):
                            st.markdown(f"**检索到的关联信息：**\n\n{context}")
                    
                    # 保存到历史
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "context": context
                    })
                else:
                    st.error(f"服务暂时不可用 (状态码: {response.status_code})")
                    
            except Exception as e:
                st.error(f"发生连接错误: {e}")
                st.markdown("请检查后端服务 `uvicorn` 是否已启动。")



# # Streamlit 前端：问答界面，调用后端 API
# """
# 运行方式（在项目根目录）：
#     streamlit run frontend/streamlit_app.py
# """
# import streamlit as st
# import requests  # 新增：用于发送 API 请求
# from typing import Optional

# # 后端 API 基础 URL
# API_BASE = "http://127.0.0.1:8000"  # 建议使用明确的 IP 而非 localhost，避免某些网络解析问题


# def call_qa_api(question: str, max_hops: int = 2, temperature: float = 0.7) -> Optional[dict]:
#     """
#     调用后端 POST /qa 接口。
#     """
#     url = f"{API_BASE}/chat"
#     payload = {
#         "query": question,
#         # "max_hops": max_hops,
#         # "temperature": temperature
#     }
    
#     try:
#         # 发送 POST 请求
#         response = requests.post(url, json=payload, timeout=60) # 设置超时防止无限等待
        
#         if response.status_code == 200:
#             data= response.json();
#             return {
#                 "answer": data.get("answer"),
#                 "graph_context": data.get("context"), # 将后端的 context 映射过来
#                 "sources": [] # 目前后端没有返回结构化的 sources，先给空列表防止前端报错
#             }
#         else:
#             st.error(f"API 请求失败，状态码：{response.status_code}")
#             st.text(response.text) # 显示后端返回的错误详情
#             return None
            
#     except requests.exceptions.ConnectionError:
#         st.error(f"无法连接到后端 ({url})。请确认后端服务已启动。")
#         return None
#     except Exception as e:
#         st.error(f"发生错误: {str(e)}")
#         return None


# def render_sidebar():
#     """侧边栏：配置参数"""
#     st.sidebar.title("设置")
    
#     # 让用户可以动态调整参数
#     max_hops = st.sidebar.slider("图谱检索跳数 (max_hops)", min_value=1, max_value=5, value=2)
#     temperature = st.sidebar.slider("模型温度 (temperature)", min_value=0.0, max_value=1.0, value=0.7)
    
#     return max_hops, temperature


# def render_main(max_hops, temperature) -> None:
#     """主区域：问题输入、发送、答案展示。"""
#     st.title("保险+医养知识图谱问答")
#     st.caption("基于 GraphRAG 的跨领域问答")

#     # 问题输入框
#     question = st.text_area("请输入您的问题", height=100, placeholder="例如：70岁老人推荐哪些重疾保险？")
    
#     col1, col2 = st.columns([1, 5])
#     with col1:
#         submitted = st.button("提交")
#     with col2:
#         # 添加一个清空按钮（可选优化）
#         if st.button("重置"):
#             st.rerun()

#     if submitted and question.strip():
#         with st.spinner("正在分析意图并检索知识图谱..."):
#             # 真正调用 API
#             result = call_qa_api(question.strip(), max_hops, temperature)
            
#             if result:
#                 # 1. 展示最终回答
#                 st.subheader("🤖 AI 回答")
#                 st.markdown(result.get("answer", "未返回回答"))
                
#                 st.divider()
                
#                 # 2. 展示参考来源（Sources）- 使用折叠面板保持界面整洁
#                 with st.expander("📚 参考来源 (三元组 evidence)"):
#                     sources = result.get("sources", [])
#                     if sources:
#                         st.dataframe(sources, column_config={
#                             "0": "头实体",
#                             "1": "关系",
#                             "2": "尾实体"
#                         }, use_container_width=True)
#                     else:
#                         st.write("无明确图谱来源")

#                 # 3. 展示图谱上下文（可选调试信息）
#                 if "graph_context" in result:
#                     with st.expander("🕸️ 图谱检索上下文 (Debug)"):
#                         st.text(result["graph_context"])
                        
#     elif submitted:
#         st.warning("请输入问题内容。")


# def main() -> None:
#     """应用入口。"""
#     # 获取侧边栏配置
#     max_hops, temperature = render_sidebar()
#     # 渲染主界面，并传入配置
#     render_main(max_hops, temperature)


# if __name__ == "__main__":
#     st.set_page_config(page_title="KG-RAG 问答系统", layout="wide") # 宽屏模式体验更好
#     main()