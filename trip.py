import requests
import os
from dotenv import load_dotenv
import streamlit as st  # 新增：导入Streamlit

# 加载API密钥
load_dotenv()
API_KEY = os.getenv("DASHSCOPE_API_KEY")

# ===== 新增调试代码 =====
print("读取到的API Key：", API_KEY)  # 终端会打印Key，确认不是None
# ========== 核心：保留原来的LLM调用逻辑 ==========
def call_llm_api(user_need):
    prompt = f"""
    你是一个专业的旅行助手，需要根据用户需求生成详细且实用的旅行行程。
    要求：
    1. 行程按「天数+时间段」拆分（如Day1 上午/下午/晚上）；
    2. 结合预算推荐性价比高的景点、美食、交通方式；
    3. 适配用户的偏好（如亲子优先推荐儿童乐园，美食优先推荐本地特色店）；
    4. 语言简洁，避免冗余，用中文输出，排版清晰。

    用户需求：{user_need}
    """

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-turbo",
        "input": {"messages": [{"role": "user", "content": prompt}]},
        "parameters": {"temperature": 0.7, "top_p": 0.8}
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # ===== 核心修改：兼容两种返回格式 =====
        # 先尝试取格式1（choices），取不到就取格式2（text）
        travel_text = ""
        if "output" in result:
            # 格式1：output → choices → message → content
            if "choices" in result["output"] and len(result["output"]["choices"]) > 0:
                travel_text = result["output"]["choices"][0]["message"]["content"]
            # 格式2：output → text
            elif "text" in result["output"]:
                travel_text = result["output"]["text"]

        if travel_text:
            return travel_text
        else:
            return f"API返回无行程内容！返回内容：{result}"
        # ======================================
    except Exception as e:
        return f"生成行程时出错啦：{str(e)}，API返回内容：{response.text if 'response' in locals() else '无响应'}"

# ========== 新增：Streamlit网页界面 ==========
def main():
    # 1. 设置网页标题、图标（可选）
    st.set_page_config(
        page_title="旅行助手智能体",
        page_icon="✈️",
        layout="wide"  # 宽屏显示
    )

    # 2. 网页头部标题
    st.title("✈️ 旅行助手智能体")
    st.subheader("输入你的旅行需求，一键生成专属行程", divider="blue")

    # 3. 输入区域：用Streamlit组件替代命令行输入
    with st.container(border=True):  # 带边框的输入框容器，更美观
        col1, col2 = st.columns(2)  # 分两列布局，更紧凑
        with col1:
            destination = st.text_input("📍 旅行目的地", placeholder="如：成都、大理、三亚")
            days = st.text_input("📅 出行天数", placeholder="如：3天、5天")
        with col2:
            budget = st.text_input("💰 人均预算", placeholder="如：800元、2000元")
            preference = st.text_input("❤️ 旅行偏好", placeholder="如：美食、亲子、徒步、打卡景点")

    # 4. 生成按钮
    generate_btn = st.button("🚀 生成专属行程", type="primary")  # 蓝色主按钮

    # 5. 点击按钮后执行逻辑
    if generate_btn:
        # 校验必填项（避免空输入）
        if not destination or not days:
            st.warning("⚠️ 目的地和出行天数不能为空哦！")
        else:
            # 整理用户需求
            user_need = f"""
            - 目的地：{destination}
            - 出行天数：{days}
            - 人均预算：{budget if budget else "无"}
            - 偏好：{preference if preference else "无"}
            """
            # 显示加载状态
            with st.spinner("正在为你生成专属行程，请稍等..."):
                travel_plan = call_llm_api(user_need)

            # 展示结果
            st.subheader("你的专属旅行行程", divider="green")
            st.markdown(travel_plan)  # 用markdown展示，排版更友好


if __name__ == "__main__":
    main()