"""
三省六部制多AI Agent系统 - Web界面
使用Streamlit创建简洁的用户界面
"""
import streamlit as st
import re
from core_architecture import build_workflow
from langchain_core.messages import HumanMessage

def extract_section(text: str, section_name: str) -> str:
    """从反思报告中提取指定部分的内容"""
    section_markers = [
        "执行效率分析",
        "结果质量评估",
        "系统优化建议",
        "潜在风险识别"
    ]
    next_marker = "|".join([re.escape(m) for m in section_markers if m != section_name])
    pattern = rf"{re.escape(section_name)}[:：](.*?)(?=\n(?:{next_marker})[:：]|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        result = match.group(1).strip()
        return result if result else "暂无相关内容"
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
        # 1. 实时状态容器（运行时显示部门行动）
        status_box = st.empty()
        progress_container = st.container()
        with progress_container:
            status_log = st.empty()

        # 2. 初始化状态
        initial_state = {
            "user_task": user_task,
            "loop_count": 0,
            "audit_status": "pending",
            "execution_stage": "plan",
            "messages": [HumanMessage(content=user_task)],
            "zhongshu_plan": "",
            "menxia_audit_result": "",
            "shangshu_result": "",
            "liubo_results": {},
            "reflection_report": "",
            "search_results": "",
            "web_content": "",
            "final_deliverable": "",
            "libu_doc_full": "",
            # 工部审批相关初始状态
            "gongbu_approval_request": "",
            "optimized_plan": "",
            "needs_approval": False,
            "gongbu_approval_status": "",
            "user_confirmation_result": "",
            "approval_timeout": False,
            "department_feedback": {}
        }

        # 3. 流式执行（核心！解决运行时看不到进度的问题）
        final_result = initial_state.copy()
        status_box.info("🔄 系统启动，正在执行任务...")

        try:
            # 用stream流式获取每个节点的执行结果，实时更新状态
            for event in st.session_state.app.stream(initial_state):
                node_name = list(event.keys())[0]
                node_data = event[node_name]
                final_result.update(node_data)

                # 实时更新部门执行日志
                if node_name == "zhongshu_plan":
                    status_log.markdown("🏛️ 中书省：正在分析任务，制定执行方案...")
                elif node_name == "menxia_audit":
                    status_log.markdown("⚖️ 门下省：正在审核方案可行性...")
                elif node_name == "shangshu_execute":
                    status_log.markdown("🏛️ 尚书省：正在调度对应部门执行任务...")
                elif node_name == "hubu_node":
                    status_log.markdown("📂 户部：正在处理数据、管理资料...")
                elif node_name == "libu_doc":
                    status_log.markdown("📝 礼部：正在撰写、润色最终成果...")
                elif node_name == "bingbu_node":
                    status_log.markdown("🔍 兵部：正在执行联网搜索、攻坚任务...")
                elif node_name == "xingbu_node":
                    status_log.markdown("⚠️ 刑部：正在执行合规校验、事实核查...")
                elif node_name == "libu_node":
                    status_log.markdown("📋 吏部：正在执行人事协调、绩效管理...")
                elif node_name == "gongbu_node":
                    status_log.markdown("🔧 工部：正在收集反馈、生成优化方案...")
                elif node_name == "reflection":
                    status_log.markdown("🔍 系统：正在生成执行反思报告...")

            # 执行完成，清空状态，显示最终结果
            status_box.success("✅ 任务执行完成！")
            status_log.empty()

            # 4. 前置最终成果（用户最关心的内容，放在最前面）
            st.divider()
            st.header("🎯 最终交付成果")
            # 优先显示礼部润色的完整内容，其次是最终交付物
            final_content = final_result.get('libu_doc_full', final_result.get('final_deliverable', '暂无生成内容'))
            st.markdown(final_content)

            # 5. 折叠起来的详细过程（只有用户想看的时候展开）
            st.divider()
            with st.expander("📂 查看详细执行过程", expanded=False):
                tab1, tab2, tab3, tab4 = st.tabs(["核心流程", "联网搜索", "系统反思", "工部审批"])

                # 核心流程标签页
                with tab1:
                    with st.expander("🏛️ 中书省 - 决策方案", expanded=False):
                        st.text_area("方案内容", final_result.get('zhongshu_plan', '暂无'), height=300, disabled=True)
                    with st.expander("⚖️ 门下省 - 审核结果", expanded=False):
                        st.text_area("审核内容", final_result.get('menxia_audit_result', '暂无'), height=200, disabled=True)
                        st.metric("方案驳回次数", final_result.get('loop_count', 0))
                    with st.expander("🏛️ 尚书省 - 执行调度", expanded=False):
                        st.text_area("执行成果", final_result.get('shangshu_result', '暂无'), height=300, disabled=True)
                    with st.expander("👥 六部执行详情", expanded=False):
                        liubo_results = final_result.get('liubo_results', {})
                        for dept, res in liubo_results.items():
                            st.markdown(f"**{dept}**")
                            st.write(res)
                            st.divider()

                # 联网搜索标签页
                with tab2:
                    search_res = final_result.get('search_results', '暂无搜索结果')
                    if search_res and search_res != '任务分析显示无需联网搜索':
                        st.markdown(search_res)
                    else:
                        st.info("本次任务无需联网搜索")

                # 系统反思标签页
                with tab3:
                    reflection = final_result.get('reflection_report', '暂无反思报告')
                    if reflection and reflection != '暂无反思报告':
                        st.markdown("### 📊 执行效率分析")
                        st.text_area("效率评估", extract_section(reflection, "执行效率分析"), height=150, disabled=True)
                        st.markdown("### 🎯 结果质量评估")
                        st.text_area("质量评估", extract_section(reflection, "结果质量评估"), height=150, disabled=True)
                        st.markdown("### 💡 系统优化建议")
                        st.text_area("优化建议", extract_section(reflection, "系统优化建议"), height=150, disabled=True)
                        st.markdown("### ⚠️ 潜在风险识别")
                        st.text_area("风险识别", extract_section(reflection, "潜在风险识别"), height=150, disabled=True)
                    else:
                        st.info("本次任务无反思报告")

                # 工部审批标签页
                with tab4:
                    approval_request = final_result.get('gongbu_approval_request', '')
                    optimized_plan = final_result.get('optimized_plan', '')
                    if approval_request:
                        st.markdown("### 📋 审批申请")
                        st.text_area("申请内容", approval_request, height=200, disabled=True)
                    if optimized_plan:
                        st.markdown("### 🛠️ 优化方案")
                        st.text_area("方案内容", optimized_plan, height=300, disabled=True)
                    # 审批状态
                    approval_status = final_result.get('gongbu_approval_status', '')
                    user_confirm = final_result.get('user_confirmation_result', '')
                    if approval_status:
                        st.metric("尚书省审批", "已批准" if "approved" in approval_status else "已驳回")
                    if user_confirm:
                        confirm_text = "已批准" if user_confirm == "approved" else "已拒绝"
                        if user_confirm == "timeout":
                            confirm_text = "审批超时"
                        st.metric("用户最终确认", confirm_text)

        except Exception as e:
            status_box.error(f"执行失败：{str(e)}")
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
    3. 实时查看部门执行进度
    4. 查看最终交付成果
    5. 可展开查看详细执行过程
    """)

if __name__ == "__main__":
    pass
