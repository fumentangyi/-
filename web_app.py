"""
三省六部制多AI Agent系统 - Web界面
使用Streamlit创建简洁的用户界面
"""

import streamlit as st
import re
from core_architecture import build_workflow

def extract_section(text: str, section_name: str) -> str:
    """从反思报告中提取指定部分的内容"""
    # 关键节标题集（用于定位下一个部分的边界）
    section_markers = [
        "执行效率分析",
        "结果质量评估",
        "系统优化建议",
        "潜在风险识别"
    ]
    # 构造匹配下一节标题的正则
    next_marker = "|".join([re.escape(m) for m in section_markers if m != section_name])
    pattern = rf"{re.escape(section_name)}[:：](.*?)(?=\n(?:{next_marker})[:：]|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        result = match.group(1).strip()
        return result if result else "暂无相关内容"
    # 如果没有找到（可能格式不同），返回全文作为后备
    return text.strip()

# 设置页面
st.set_page_config(
    page_title="三省六部制AI Agent",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ 三省六部制多AI Agent系统")
st.markdown("基于中国古代三省六部制的智能任务执行系统")

# 初始化工作流
if 'app' not in st.session_state:
    st.session_state.app = build_workflow()

# 用户输入区域
st.header("📝 任务输入")
user_task = st.text_area(
    "请输入您的任务描述：",
    placeholder="例如：写一篇关于人工智能发展趋势的论文",
    height=100
)

# 执行按钮
if st.button("🚀 开始执行", type="primary", use_container_width=True):
    if not user_task.strip():
        st.error("请输入任务描述！")
    else:
            with st.spinner("正在执行任务，请稍候..."):
                # 初始化状态
                initial_state = {
                    "user_task": user_task,
                    "loop_count": 0,
                    "audit_status": "pending",
                    "execution_stage": "plan",
                    "messages": [],
                    "zhongshu_plan": "",
                    "menxia_audit_result": "",
                    "shangshu_result": "",
                    "liubo_results": {},
                    "reflection_report": "",
                    "search_results": "",
                    "web_content": "",
                    "final_deliverable": "",
                    # 工部审批相关初始状态
                    "gongbu_approval_request": "",
                    "optimized_plan": "",
                    "needs_approval": False,
                    "gongbu_approval_status": "",
                    "user_confirmation_result": "",
                    "approval_timeout": False,
                    "department_feedback": {}
                }

            # 运行系统
            try:
                result = st.session_state.app.invoke(initial_state)

                # 显示结果
                st.success("任务执行完成！")

                # 创建选项卡显示结果
                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🌐 联网搜索", "📋 执行方案", "✅ 审核结果", "📊 执行成果", "🏁 最终成果", "📈 六部详情", "🔍 系统反思", "🔧 工部审批"])

                with tab1:
                    st.subheader("🌐 联网搜索结果")
                    search_results = result.get('search_results', '暂无搜索结果')
                    if search_results and search_results != '任务分析显示无需联网搜索':
                        st.markdown(search_results)
                    else:
                        st.info("本次任务无需联网搜索")

                with tab2:
                    st.subheader("中书省执行方案")
                    st.text_area("方案内容", result['zhongshu_plan'], height=300, disabled=True)

                with tab3:
                    st.subheader("门下省审核结果")
                    st.text_area("审核内容", result['menxia_audit_result'], height=200, disabled=True)
                    st.metric("驳回次数", result['loop_count'])

                with tab4:
                    st.subheader("尚书省执行成果")
                    st.text_area("成果内容", result['shangshu_result'], height=300, disabled=True)

                with tab5:
                    st.subheader("🏁 最终成果")
                    final_deliverable = result.get('final_deliverable', '暂无最终成果')
                    st.text_area("最终成果摘要", final_deliverable, height=250, disabled=True)

                with tab6:
                    st.subheader("六部执行详情")
                    liubo_results = result.get('liubo_results', {})
                    for dept, result_text in liubo_results.items():
                        with st.expander(f"🏛️ {dept}"):
                            st.write(result_text)

                with tab7:
                    st.subheader("🔍 系统反思报告")
                    reflection = result.get('reflection_report', '暂无反思报告')
                    if reflection and reflection != '暂无反思报告':
                        # 解析反思报告，按维度展示
                        st.markdown("### 📊 执行效率分析")
                        st.text_area("效率评估", extract_section(reflection, "执行效率分析"), height=150, disabled=True)

                        st.markdown("### 🎯 结果质量评估")
                        st.text_area("质量评估", extract_section(reflection, "结果质量评估"), height=150, disabled=True)

                        st.markdown("### 💡 系统优化建议")
                        st.text_area("优化建议", extract_section(reflection, "系统优化建议"), height=150, disabled=True)

                        st.markdown("### ⚠️ 潜在风险识别")
                        st.text_area("风险识别", extract_section(reflection, "潜在风险识别"), height=150, disabled=True)
                    else:
                        st.info("系统正在生成反思报告...")
                        st.text_area("反思内容", reflection, height=200, disabled=True)

                with tab8:
                    st.subheader("🔧 工部技术方案审批")
                    approval_request = result.get('gongbu_approval_request', '')
                    optimized_plan = result.get('optimized_plan', '')
                    department_feedback = result.get('department_feedback', {})

                    if approval_request:
                        st.markdown("### 📋 审批申请")
                        st.text_area("申请内容", approval_request, height=200, disabled=True)

                    if optimized_plan:
                        st.markdown("### 🛠️ 优化方案")
                        st.text_area("方案内容", optimized_plan, height=300, disabled=True)

                    if department_feedback:
                        st.markdown("### 📊 各部门反馈")
                        for dept, feedback in department_feedback.items():
                            with st.expander(f"🏛️ {dept} 反馈"):
                                st.write(feedback)

                    # 审批状态显示
                    approval_status = result.get('gongbu_approval_status', '')
                    user_confirmation = result.get('user_confirmation_result', '')

                    col1, col2 = st.columns(2)
                    with col1:
                        if approval_status:
                            status_text = "已批准" if "approved" in approval_status else "已驳回"
                            st.metric("尚书省审批", status_text)
                    with col2:
                        if user_confirmation:
                            confirm_text = "已批准" if user_confirmation == "approved" else "已拒绝"
                            if user_confirmation == "timeout":
                                confirm_text = "超时"
                            st.metric("用户确认", confirm_text)

            except Exception as e:
                st.error(f"执行过程中出现错误：{str(e)}")
                st.exception(e)

# 侧边栏信息
with st.sidebar:
    st.header("ℹ️ 系统信息")
    st.markdown("""
    **三省六部制AI Agent系统**

    - 🏛️ **中书省**：决策规划
    - ⚖️ **门下省**：审核校验
    - 🏛️ **尚书省**：执行调度
    - 👥 **六部**：具体执行

    **工部审批机制：**
    - 📊 收集各部门反馈
    - 🛠️ 生成优化方案
    - ✅ 尚书省审批
    - ⚖️ 门下省审核
    - 👤 用户最终确认

    **支持的任务类型：**
    - 论文写作
    - 项目规划
    - 代码开发
    - 研究分析
    """)

    st.header("🔧 使用说明")
    st.markdown("""
    1. 在上方输入框描述您的任务
    2. 点击"开始执行"按钮
    3. 等待系统自动完成任务
    4. 查看各阶段的执行结果
    5. 工部方案需要用户确认
    """)

if __name__ == "__main__":
    pass