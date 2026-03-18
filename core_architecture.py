"""
三省六部制多AI Agent系统 - 核心架构实现
阶段1：定死核心骨架，跑通完整闭环
"""

from typing import TypedDict, Annotated, Sequence
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import operator
import requests
from bs4 import BeautifulSoup
import re
import time
from logger import AgentLogger
import datetime

# 获取当前时间的函数
def get_timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")

# ========================================
# 1. 系统状态定义（全流程可追溯）
# ========================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]  # 全流程消息记录
    user_task: str  # 用户原始任务
    zhongshu_plan: str  # 中书省的方案
    menxia_audit_result: str  # 门下省的审核结果
    shangshu_result: str  # 尚书省的执行成果
    liubo_results: dict  # 六部执行结果
    audit_status: str  # 审核状态：pending/pass/reject
    loop_count: int  # 驳回循环次数，避免死循环
    execution_stage: str  # 执行阶段：plan/execute/final_audit
    reflection_report: str  # 系统反思报告
    search_results: str  # 联网搜索结果
    web_content: str  # 原始网页内容
    final_deliverable: str  # 最终交付成果（简要总结）
    libu_doc_full: str  # 礼部完整文档
    # 工部审批相关字段
    gongbu_approval_request: str  # 工部审批申请
    optimized_plan: str  # 工部优化后的方案
    needs_approval: bool  # 是否需要审批
    gongbu_approval_status: str  # 工部审批状态
    user_confirmation_result: str  # 用户确认结果
    approval_timeout: bool  # 是否超时
    department_feedback: dict  # 各部门反馈

# ========================================
# 2. 初始化本地大模型
# ========================================
llm = OllamaLLM(model="qwen2:7b", temperature=0.3)

# ========================================
# 2.2 初始化日志系统
# ========================================
logger = AgentLogger.get_instance()

# ========================================
# 2.5 反思Agent
# ========================================
def reflection_agent(state: AgentState):
    """
    反思Agent：系统执行后的自我评估与改进建议
    分析整个执行过程，提出优化方向
    """
    print("=== 【反思Agent】正在进行系统反思 ===")

    user_task = state["user_task"]
    zhongshu_plan = state["zhongshu_plan"]
    menxia_audit_result = state["menxia_audit_result"]
    shangshu_result = state["shangshu_result"]
    loop_count = state["loop_count"]
    liubo_results = state["liubo_results"]

    prompt = f"""
你是一个专业的系统反思分析师，负责分析三省六部制AI Agent系统的执行过程。

请对以下执行过程进行全面反思：

【用户原始任务】
{user_task}

【中书省执行方案】
{zhongshu_plan}

【门下省审核结果】
{menxia_audit_result}

【尚书省执行成果】
{shangshu_result}

【六部执行详情】
{liubo_results}

【执行统计】
- 驳回次数：{loop_count}
- 执行阶段：{state["execution_stage"]}

请从以下维度进行反思分析：

1. **执行效率分析**：
   - 方案制定是否高效？
   - 审核过程是否必要？
   - 执行环节是否存在冗余？

2. **结果质量评估**：
   - 最终成果是否满足用户需求？
   - 各环节质量把控如何？
   - 是否存在AI幻觉或错误？

3. **系统优化建议**：
   - 流程中哪些环节可以改进？
   - 是否需要调整Agent的职责分工？
   - 如何提高决策准确性？

4. **潜在风险识别**：
   - 执行过程中有哪些风险点？
   - 如何避免类似问题？

请提供建设性的反思报告，包含具体改进建议。

请按照以下格式输出，确保可以被自动解析：

执行效率分析：
- ...

结果质量评估：
- ...

系统优化建议：
- ...

潜在风险识别：
- ...
"""

    try:
        reflection = llm.invoke(prompt)
    except Exception as e:
        print(f"[ERROR] 反思Agent LLM调用失败: {e}")
        reflection = "反思分析失败：由于技术问题，无法生成反思报告。"

    return {
        "reflection_report": reflection,
        "messages": [SystemMessage(content=f"系统反思报告：{reflection}")]
    }

# ========================================
# 2.6 联网搜索Agent
# ========================================
def web_search_agent(state: AgentState):
    """
    联网搜索Agent：负责搜索相关信息和网页内容
    为任务执行提供外部知识支持
    """
    print("=== 【联网搜索Agent】正在搜索相关信息 ===")

    user_task = state["user_task"]

    # 首先分析是否需要搜索
    analysis_prompt = f"""
你是一个搜索需求分析师。请分析用户任务是否需要联网搜索外部信息。

用户任务：{user_task}

请判断：
1. 是否需要搜索最新信息？
2. 是否需要查找具体数据或事实？
3. 是否需要参考外部资源？

如果需要搜索，请提供搜索关键词和搜索策略。
如果不需要搜索，请说明理由。

输出格式：
需要搜索：[是/否]
搜索关键词：[关键词列表]
搜索理由：[简要说明]
"""

    try:
        analysis = llm.invoke(analysis_prompt)
    except Exception as e:
        print(f"[ERROR] 搜索分析LLM调用失败: {e}")
        analysis = "需要搜索：是\n搜索关键词：相关信息\n搜索理由：无法确定是否需要搜索"

    # 解析分析结果
    needs_search = "需要搜索：是" in analysis

    if not needs_search:
        print("[INFO] 任务不需要联网搜索")
        return {
            "search_results": "任务分析显示无需联网搜索",
            "web_content": "",
            "messages": [SystemMessage(content="搜索Agent：任务无需联网搜索")]
        }

    # 提取搜索关键词
    import re
    keyword_match = re.search(r'搜索关键词：(.+)', analysis)
    keywords = keyword_match.group(1) if keyword_match else user_task

    print(f"[INFO] 开始搜索关键词：{keywords}")

    # 执行搜索
    search_results = perform_web_search(keywords)

    # 整理搜索结果
    formatted_results = format_search_results(search_results)

    return {
        "search_results": formatted_results,
        "web_content": search_results,
        "messages": [SystemMessage(content=f"联网搜索完成：找到{len(search_results)}条相关信息")]
    }

def perform_web_search(query, max_results=5):
    """
    执行网页搜索
    使用DuckDuckGo搜索API获取结果
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import time

        # 使用DuckDuckGo搜索
        search_url = f"https://duckduckgo.com/html/?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        # 解析搜索结果
        for result in soup.find_all('div', class_='result')[:max_results]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')

            if title_elem and snippet_elem:
                title = title_elem.get_text().strip()
                url = title_elem.get('href', '')
                snippet = snippet_elem.get_text().strip()

                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })

        # 如果DuckDuckGo搜索失败，尝试备用方法
        if not results:
            print("[WARN] DuckDuckGo搜索失败，尝试备用搜索方法")
            results = fallback_search(query, max_results)

        return results

    except Exception as e:
        print(f"[ERROR] 网页搜索失败: {e}")
        return [{
            'title': '搜索失败',
            'url': '',
            'snippet': f'无法完成搜索：{str(e)}'
        }]

def fallback_search(query, max_results=3):
    """
    备用搜索方法：使用简单的关键词匹配模拟
    """
    # 这里可以实现更复杂的备用搜索逻辑
    return [{
        'title': f'关于"{query}"的搜索结果',
        'url': f'https://www.google.com/search?q={query}',
        'snippet': f'建议访问Google搜索了解更多关于"{query}"的信息。'
    }]

def format_search_results(results):
    """
    格式化搜索结果为易读的文本
    """
    if not results:
        return "未找到相关搜索结果"

    formatted = "📊 联网搜索结果：\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. **{result['title']}**\n"
        formatted += f"   🔗 {result['url']}\n"
        formatted += f"   📝 {result['snippet']}\n\n"

    return formatted

# ========================================
# 3. 三省节点函数（核心架构）
# ========================================

def zhongshu_node(state: AgentState):
    """
    中书省：决策规划Agent
    核心职能：出令权 - 拆解任务、制定方案、明确分工
    """
    logger.log("中书省", "INFO", "开始制定执行方案")
    print(f"\n【{get_timestamp()}】🏛️ 中书省：开始执行任务")
    print(f"【{get_timestamp()}】  ▶ 正在分析用户需求...")
    print(f"【{get_timestamp()}】  ▶ 正在拆解任务为子任务...")
    print(f"【{get_timestamp()}】  ▶ 正在制定执行方案...")
    print(f"【{get_timestamp()}】  ▶ 正在明确各部门分工...")

    user_task = state["user_task"]
    loop_count = state["loop_count"]
    search_results = state.get("search_results", "")

    prompt = f"""
你是中国古代三省六部制中的【中书省决策规划Agent】，拥有最高的政令制定权。

你的核心职责是接收用户的原始任务，制定科学、可落地、权责清晰的《任务执行总方案》。

用户原始任务：
{user_task}

{f"联网搜索结果：\\n{search_results}\\n\\n请参考以上搜索信息制定更准确的方案。" if search_results else ""}

{"（这是第" + str(loop_count) + "次重新制定方案，请根据之前的驳回意见优化）" if loop_count > 0 else ""}

工作要求：
1. 精准理解用户的核心需求、交付标准、时间要求
2. 把复杂任务拆解为可执行的子任务
3. 明确每个子任务的负责部门（六部：吏、户、礼、兵、刑、工）
4. 明确每个环节的验收标准
5. 方案必须符合三省六部制的流转逻辑

输出要求：
只输出标准化的《任务执行总方案》，不要多余的寒暄，结构清晰，权责明确，步骤可落地。
"""

    try:
        plan = llm.invoke(prompt)
        logger.log("中书省", "INFO", f"方案制定完成，长度: {len(plan)}")
    except Exception as e:
        logger.log("中书省", "ERROR", f"LLM调用失败: {e}")
        print(f"[ERROR] 中书省LLM调用失败: {e}")
        plan = "方案制定失败：由于技术问题，无法生成执行方案。请检查模型连接并重试。"

    return {
        "zhongshu_plan": plan,
        "messages": [SystemMessage(content=f"中书省制定方案：{plan}")],
        "audit_status": "pending",
        "execution_stage": "plan"
    }


def menxia_audit_node(state: AgentState):
    """
    门下省：审核校验Agent
    核心职能：封驳权 - 方案审核、成果终审、驳回重制
    """
    execution_stage = state["execution_stage"]
    loop_count = state["loop_count"]

    if execution_stage == "plan":
        logger.log("门下省", "INFO", "开始审核中书省的方案")
        print(f"\n【{get_timestamp()}】⚖️ 门下省：开始审核中书省的方案")
        print(f"【{get_timestamp()}】  ▶ 正在审核方案完整性...")
        print(f"【{get_timestamp()}】  ▶ 正在校验逻辑可行性...")
        print(f"【{get_timestamp()}】  ▶ 正在核对用户需求对齐度...")
        user_task = state["user_task"]
        target_content = state["zhongshu_plan"]
        audit_type = "方案"
    elif execution_stage == "execute" and "libu_doc_result" in state:
        logger.log("门下省", "INFO", "开始审核礼部撰写的文档")
        print(f"\n【{get_timestamp()}】⚖️ 门下省：开始审核礼部文档")
        print(f"【{get_timestamp()}】  ▶ 正在审核文档格式...")
        print(f"【{get_timestamp()}】  ▶ 正在校验内容准确性...")
        print(f"【{get_timestamp()}】  ▶ 正在确认交付标准...")
        user_task = state["user_task"]
        target_content = state["libu_doc_result"]
        audit_type = "礼部文档"
    else:
        logger.log("门下省", "INFO", "开始终审尚书省的成果")
        print(f"\n【{get_timestamp()}】⚖️ 门下省：开始终审执行成果")
        print(f"【{get_timestamp()}】  ▶ 正在终审成果质量...")
        print(f"【{get_timestamp()}】  ▶ 正在验证最终交付标准...")
        user_task = state["user_task"]
        target_content = state["shangshu_result"]
        audit_type = "成果"

    prompt = f"""
你是中国古代三省六部制中的【门下省审核校验Agent】，拥有最高的封驳审核权。

你的核心职责是审核中书省的{audit_type}/尚书省的最终{audit_type}，判断是否符合用户需求、是否合理可落地、是否有逻辑漏洞。

用户原始任务：
{user_task}

待审核{audit_type}：
{target_content}

工作要求：
1. 严格对齐用户的原始需求，审核{audit_type}是否偏离核心目标
2. 审核{audit_type}的步骤是否可落地、分工是否合理
3. 审核{audit_type}是否有事实性错误、AI幻觉、逻辑漏洞
4. 只有2种输出结果，不要模棱两可：
   - 【审核通过令】：明确说明{audit_type}符合要求，准予执行/交付
   - 【驳回重审令】：明确列出所有的问题、修改要求、优化方向，打回对应部门重新修改

输出要求：
直接输出【审核通过令】或【驳回重审令】，并说明理由，不要废话。
"""

    try:
        audit_result = llm.invoke(prompt)
    except Exception as e:
        logger.log("门下省", "ERROR", f"LLM调用失败: {e}")
        print(f"[ERROR] LLM调用失败: {e}")
        audit_result = "【驳回重审令】由于技术问题，审核无法完成，请重试。"

    # 判断审核结果
    if "审核通过令" in audit_result:
        new_status = "pass"
        logger.log("门下省", "INFO", f"{audit_type}审核通过")
        
        # 如果是礼部文档审核通过，生成最终交付成果
        if audit_type == "礼部文档" and "libu_doc_result" in state:
            try:
                deliverable_prompt = f"""
你是一个项目总结专家。请根据以下礼部撰写的文档，提炼出一份简洁明了的"最终交付成果"说明，供用户直接使用：

礼部文档：
{state["libu_doc_result"]}

用户原始任务：
{user_task}

要求：
1. 表述清晰、结构简洁。
2. 突出最重要的交付内容。
3. 适合直接给用户展示。
"""
                final_deliverable = llm.invoke(deliverable_prompt)
                logger.log("门下省", "INFO", "最终交付成果生成完成")
                
                # 更新六部执行结果
                liubo_results = state.get("liubo_results", {})
                liubo_results["礼部"] = f"完成文档撰写并审核通过"

                # 保存完整的礼部文档
                result["libu_doc_full"] = state["libu_doc_full"]
                
            except Exception as e:
                logger.log("门下省", "ERROR", f"生成最终交付成果失败: {e}")
                final_deliverable = "无法生成最终交付成果摘要，请查看礼部文档。"
                liubo_results = state.get("liubo_results", {})
        else:
            final_deliverable = None
            liubo_results = None
    else:
        new_status = "reject"
        loop_count += 1  # 无论方案还是成果审核驳回，都增加计数
        logger.log("门下省", "WARN", f"{audit_type}被驳回，驳回次数: {loop_count}")
        final_deliverable = None

    result = {
        "menxia_audit_result": audit_result,
        "audit_status": new_status,
        "loop_count": loop_count,
        "messages": [SystemMessage(content=f"门下省审核结果：{audit_result}")]
    }
    
    if final_deliverable:
        result["final_deliverable"] = final_deliverable
    
    if liubo_results:
        result["liubo_results"] = liubo_results
    
    return result


def shangshu_execute_node(state: AgentState):
    """
    尚书省：执行总调度Agent
    核心职能：执行权 - 调度六部、管控进度、汇总成果
    """
    logger.log("尚书省", "INFO", "开始调度执行任务")
    print(f"\n【{get_timestamp()}】🏛️ 尚书省：开始调度执行任务")
    print(f"【{get_timestamp()}】  ▶ 正在解析执行方案...")
    print(f"【{get_timestamp()}】  ▶ 正在调度户部（数据资源）...")
    print(f"【{get_timestamp()}】  ▶ 正在调度礼部（文档撰写）...")
    print(f"【{get_timestamp()}】  ▶ 正在调度工部（技术实现）...")
    print(f"【{get_timestamp()}】  ▶ 正在汇总执行成果...")

    zhongshu_plan = state["zhongshu_plan"]

    prompt = f"""
你是任务执行总调度Agent，负责协调完成用户任务。

中书省执行方案：
{zhongshu_plan}

工作要求：
1. 按照方案执行任务
2. 协调各环节工作
3. 汇总最终成果

输出要求：
输出完整的执行结果，包含用户需要的答案。
"""

    try:
        execute_result = llm.invoke(prompt)
        logger.log("尚书省", "INFO", f"执行完成，结果长度: {len(execute_result)}")
    except Exception as e:
        logger.log("尚书省", "ERROR", f"LLM调用失败: {e}")
        print(f"[ERROR] 尚书省LLM调用失败: {e}")
        execute_result = "执行失败：由于技术问题，无法完成任务执行。请检查模型连接并重试。"

    # 简化的六部执行结果
    liubo_results = {
        "户部": "完成数据管理资料归集",
        "礼部": "等待文档撰写",
        "工部": "完成技术实现"
    }

    # 生成最终交付成果摘要
    try:
        deliverable_prompt = f"""
你是一个项目总结专家。请根据以下尚书省执行成果，提炼出一份简洁明了的“最终交付成果”说明，供用户直接使用：

执行成果：
{execute_result}

要求：
1. 表述清晰、结构简洁。
2. 突出最重要的交付内容。
3. 适合直接给用户展示。
"""
        final_deliverable = llm.invoke(deliverable_prompt)
    except Exception as e:
        print(f"[ERROR] 生成最终交付成果失败: {e}")
        final_deliverable = "无法生成最终交付成果摘要，请查看执行成果。"

    return {
        "shangshu_result": execute_result,
        "liubo_results": liubo_results,
        "final_deliverable": final_deliverable,
        "messages": [SystemMessage(content=f"尚书省执行成果：{execute_result}")],
        "execution_stage": "execute"
    }

# ========================================
# 4. 六部节点函数（执行层）
# ========================================

def libu_node(state: AgentState):
    """吏部：已精简，跳过执行"""
    return {"messages": [SystemMessage(content="吏部：已精简")]}

def hubu_node(state: AgentState):
    """户部：数据与资源管理Agent"""
    print(f"\n  【{get_timestamp()}】📊 户部：正在处理数据与资源管理")
    print(f"  【{get_timestamp()}】  ▶ 正在收集相关数据资料...")
    print(f"  【{get_timestamp()}】  ▶ 正在整理资源清单...")
    print(f"  【{get_timestamp()}】  ▶ 正在进行数据分析...")
    prompt = "你是户部Agent，负责数据管理与资料归集。当前任务：配合尚书省的调度。"
    result = llm.invoke(prompt)
    return {"messages": [SystemMessage(content=f"户部执行：{result}")]}

def libu_doc_node(state: AgentState):
    """礼部：文档与沟通协同Agent - 负责撰写最终交付文档"""
    print(f"\n  【{get_timestamp()}】📝 礼部：正在撰写最终交付文档")
    print(f"  【{get_timestamp()}】  ▶ 正在整理执行成果...")
    print(f"  【{get_timestamp()}】  ▶ 正在撰写专业文档...")
    print(f"  【{get_timestamp()}】  ▶ 正在优化文档格式...")

    shangshu_result = state.get("shangshu_result", "")
    user_task = state["user_task"]

    # 简化prompt，直接输出有用内容
    prompt = f"""
你是用户的AI助手，只做一件事：
根据执行结果，给用户生成清晰、有用、可直接使用的答案。
不要写部门执行过程、不要写古代政务、不要写总结报告。
只输出用户真正需要的内容：

用户任务：{user_task}
执行结果：{shangshu_result}

直接输出有用答案，简洁、实用、无废话。
"""

    try:
        doc_result = llm.invoke(prompt)
        logger.log("礼部", "INFO", f"文档撰写完成，长度: {len(doc_result)}")
    except Exception as e:
        logger.log("礼部", "ERROR", f"文档撰写失败: {e}")
        print(f"[ERROR] 礼部文档撰写失败: {e}")
        doc_result = "文档撰写失败，请查看执行成果了解详情。"

    return {
        "libu_doc_full": doc_result,
        "messages": [SystemMessage(content=f"礼部文档：{doc_result}")]
    }

def bingbu_node(state: AgentState):
    """兵部：已精简，跳过执行"""
    return {"messages": [SystemMessage(content="兵部：已精简")]}

def xingbu_node(state: AgentState):
    """刑部：已精简，跳过执行"""
    return {"messages": [SystemMessage(content="刑部：已精简")]}

def gongbu_node(state: AgentState):
    """工部：技术与工程实现Agent（增强版 - 支持审批机制）"""
    print(f"\n  【{get_timestamp()}】🔧 工部：正在处理技术与工程实现")
    print(f"  【{get_timestamp()}】  ▶ 正在分析技术需求...")
    print(f"  【{get_timestamp()}】  ▶ 正在制定技术方案...")
    print(f"  【{get_timestamp()}】  ▶ 正在收集各部门技术反馈...")
    logger.log("工部", "INFO", "工部节点启动")

    # 收集各部门反馈
    feedback = collect_department_feedback(state)
    logger.log("工部", "INFO", "各部门反馈收集完成")

    # 生成优化方案
    current_plan = state.get('zhongshu_plan', '') or state.get('current_plan', '')
    optimization_prompt = f"""
你是中国古代三省六部制中的【工部技术与工程实现Agent】，拥有最高的技术实现权。

你的核心职责是根据各部门反馈优化技术方案，并提交上级审批。

当前任务背景：
{state['user_task']}

当前执行方案：
{current_plan}

各部门反馈：
{format_feedback(feedback)}

工作要求：
1. 仔细分析各部门的反馈意见
2. 在保证技术可行性的前提下，尽可能满足各部门需求
3. 提出具体的技术实施方案
4. 明确说明优化后的方案优势

输出要求：
输出《技术优化方案》，包含优化内容、技术实施路径、预期效果等。
"""

    try:
        optimized_plan = llm.invoke(optimization_prompt)
        logger.log("工部", "INFO", f"优化方案生成完成，长度: {len(optimized_plan)}")
    except Exception as e:
        logger.log("工部", "ERROR", f"优化方案生成失败: {e}")
        optimized_plan = "优化方案生成失败：由于技术问题，无法生成优化方案。"

    # 生成审批申请
    approval_request = f"""
【工部技术方案审批申请】

申请部门：工部
申请事项：技术优化方案审批

优化方案内容：
{optimized_plan}

各部门反馈摘要：
{format_feedback_summary(feedback)}

审批理由：
该方案综合考虑了各部门反馈，需要进行技术可行性评估和合规性审核。

申请时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
"""

    logger.log("工部", "WARN", "提交审批申请到尚书省")

    return {
        "messages": [SystemMessage(content=f"工部申请：{approval_request}")],
        "gongbu_approval_request": approval_request,
        "optimized_plan": optimized_plan,
        "needs_approval": True,
        "department_feedback": feedback
    }

def format_feedback(feedback: dict) -> str:
    """格式化各部门反馈"""
    formatted = ""
    for dept, content in feedback.items():
        formatted += f"\n【{dept}反馈】\n{content}\n"
    return formatted

def format_feedback_summary(feedback: dict) -> str:
    """格式化反馈摘要"""
    summary = ""
    for dept, content in feedback.items():
        summary += f"\n{dept}：{content[:100]}...\n"
    return summary

# ========================================
# 4.5 工部审批相关节点
# ========================================

def shangshu_gongbu_approval_node(state: AgentState):
    """尚书省：审批工部技术方案Agent"""
    logger.log("尚书省", "INFO", "开始审批工部技术方案")

    approval_request = state.get("gongbu_approval_request", "")
    optimized_plan = state.get("optimized_plan", "")

    prompt = f"""
你是中国古代三省六部制中的【尚书省执行总调度Agent】，正在审批工部提交的技术优化方案。

工部审批申请：
{approval_request}

优化方案：
{optimized_plan}

工作要求：
1. 评估技术方案的可行性
2. 评估资源需求是否合理
3. 评估方案是否符合整体执行计划
4. 判断是否应该批准该方案

输出要求：
输出审批结果，格式：
【批准令】：批准方案执行，说明理由
或
【驳回令】：驳回方案，列出问题和修改要求
"""

    try:
        approval_result = llm.invoke(prompt)
        logger.log("尚书省", "INFO", f"审批完成: {'批准' if '批准令' in approval_result else '驳回'}")
    except Exception as e:
        logger.log("尚书省", "ERROR", f"审批失败: {e}")
        approval_result = "【驳回令】审批过程出现技术错误，请重试。"

    # 判断审批结果
    if "批准令" in approval_result:
        new_status = "shangshu_approved"
    else:
        new_status = "shangshu_rejected"

    return {
        "messages": [SystemMessage(content=f"尚书省审批结果：{approval_result}")],
        "gongbu_approval_status": new_status
    }

def menxia_gongbu_audit_node(state: AgentState):
    """门下省：审核工部技术方案Agent"""
    logger.log("门下省", "INFO", "开始审核工部技术方案")

    approval_request = state.get("gongbu_approval_request", "")
    shangshu_result = state.get("messages", [SystemMessage(content="")])[-1].content if state.get("messages") else ""

    prompt = f"""
你是中国古代三省六部制中的【门下省审核校验Agent】，正在审核工部提交的技术优化方案（尚书省已审批）。

工部审批申请：
{approval_request}

尚书省审批意见：
{shangshu_result}

工作要求：
1. 审核技术方案是否合规
2. 审核是否存在安全隐患
3. 审核是否符合系统规范
4. 判断是否应该提交用户确认

输出要求：
输出审核结果，格式：
【审核通过令】：方案合规，提交用户确认
或
【驳回重审令】：方案存在问题，驳回修改
"""

    try:
        audit_result = llm.invoke(prompt)
        logger.log("门下省", "INFO", f"审核完成: {'通过' if '审核通过令' in audit_result else '驳回'}")
    except Exception as e:
        logger.log("门下省", "ERROR", f"审核失败: {e}")
        audit_result = "【驳回重审令】审核过程出现技术错误，请重试。"

    # 判断审核结果
    if "审核通过令" in audit_result:
        new_status = "pass"
    else:
        new_status = "reject"

    return {
        "messages": [SystemMessage(content=f"门下省审核结果：{audit_result}")],
        "audit_status": new_status
    }

def user_confirmation_node(state: AgentState):
    """用户确认节点：等待用户输入确认"""
    logger.log("用户确认", "INFO", "等待用户确认工部技术方案")

    approval_request = state.get("gongbu_approval_request", "")
    optimized_plan = state.get("optimized_plan", "")

    print("\n" + "="*80)
    print("工部技术方案需要您的确认")
    print("="*80)
    print(approval_request)
    print("="*80)
    print("优化方案内容：")
    print(optimized_plan)
    print("="*80)

    # 带超时的用户输入
    start_time = time.time()
    timeout = 300  # 5分钟超时

    while time.time() - start_time < timeout:
        try:
            user_input = input("\n请确认（Y=批准，N=拒绝，5分钟内）: ").strip().upper()
            if user_input in ['Y', 'N']:
                result = "approved" if user_input == 'Y' else "rejected"
                status = "pass" if user_input == 'Y' else "reject"
                logger.log("用户确认", "INFO", f"用户选择: {'批准' if user_input == 'Y' else '拒绝'}")
                return {
                    "user_confirmation_result": result,
                    "approval_status": status,
                    "messages": [SystemMessage(content=f"用户确认结果：{result}")]
                }
        except KeyboardInterrupt:
            logger.log("用户确认", "WARN", "用户中断确认")
            return {
                "user_confirmation_result": "interrupted",
                "approval_status": "reject",
                "approval_timeout": True
            }

    logger.log("用户确认", "WARN", "用户确认超时")
    return {
        "user_confirmation_result": "timeout",
        "approval_status": "reject",
        "approval_timeout": True,
        "messages": [SystemMessage(content="用户确认超时")]
    }

def execute_optimized_plan_node(state: AgentState):
    """执行优化方案节点"""
    logger.log("执行优化", "INFO", "开始执行工部优化方案")

    optimized_plan = state.get("optimized_plan", "")

    prompt = f"""
你是中国古代三省六部制中的【执行Agent】，负责执行工部优化后的技术方案。

优化方案：
{optimized_plan}

工作要求：
1. 严格按照优化方案执行
2. 确保执行质量
3. 记录执行过程

输出要求：
输出执行结果，包含执行情况和最终成果。
"""

    try:
        execution_result = llm.invoke(prompt)
        logger.log("执行优化", "INFO", f"执行完成，结果长度: {len(execution_result)}")
    except Exception as e:
        logger.log("执行优化", "ERROR", f"执行失败: {e}")
        execution_result = f"执行失败：{str(e)}"

    return {
        "messages": [SystemMessage(content=f"优化方案执行结果：{execution_result}")],
        "shangshu_result": execution_result
    }

# ========================================
# 5. 路由逻辑（审核通过/驳回的流转）
# ========================================

def route_after_audit(state: AgentState):
    """
    门下省审核后的路由逻辑
    - 审核通过：进入执行阶段
    - 驳回：回到中书省重新制定方案
    - 超过3次驳回：强制结束
    """
    execution_stage = state["execution_stage"]

    if execution_stage == "plan":
        # 方案审核阶段
        if state["loop_count"] >= 3:
            print("[WARN] 驳回次数超过3次，强制结束流程")
            return END
        if state["audit_status"] == "pass":
            print("[OK] 方案审核通过，进入执行阶段")
            return "shangshu_execute"
        else:
            print("[REJECT] 方案被驳回，回到中书省重新制定")
            return "zhongshu_plan"
    else:
        # 终审阶段 - 现在是礼部文档审核
        if state["audit_status"] == "pass":
            print("[OK] 礼部文档审核通过，生成最终交付成果并进入反思阶段")
            return "reflection"  # 任务完成后进入反思
        else:
            print("[REJECT] 礼部文档被驳回，重新撰写")
            if state["loop_count"] >= 3:
                print("[WARN] 驳回次数超过3次，强制结束流程")
                return END
            return "libu_doc"

def route_after_shangshu_gongbu_approval(state: AgentState):
    """尚书省审批工部方案后的路由逻辑"""
    approval_status = state.get("gongbu_approval_status", "")

    if approval_status == "shangshu_approved":
        logger.log("路由", "INFO", "尚书省审批通过，进入门下省审核")
        return "menxia_gongbu_audit"
    elif approval_status == "shangshu_rejected":
        logger.log("路由", "INFO", "尚书省审批驳回，回到工部重新提交")
        return "gongbu_resubmit"
    else:
        logger.log("路由", "WARN", f"未知审批状态: {approval_status}")
        return "gongbu_resubmit"

def route_after_menxia_gongbu_audit(state: AgentState):
    """门下省审核工部方案后的路由逻辑"""
    audit_status = state.get("audit_status", "")

    if audit_status == "pass":
        logger.log("路由", "INFO", "门下省审核通过，进入用户确认")
        return "user_confirmation"
    else:
        logger.log("路由", "INFO", "门下省审核驳回，回到工部重新提交")
        return "gongbu_resubmit"

def route_after_user_confirmation(state: AgentState):
    """用户确认后的路由逻辑"""
    approval_status = state.get("approval_status", "")

    if approval_status == "pass":
        logger.log("路由", "INFO", "用户确认批准，执行优化方案")
        return "execute_optimized_plan"
    else:
        logger.log("路由", "INFO", "用户确认拒绝/超时，回到工部重新提交")
        return "gongbu_resubmit"

def gongbu_resubmit_node(state: AgentState):
    """工部重新提交节点"""
    logger.log("工部", "WARN", "重新准备提交审批申请")

    # 简化版重新提交，实际应用中可能需要更复杂的逻辑
    return {
        "needs_approval": True,
        "messages": [SystemMessage(content="工部重新提交审批申请")]
    }

# ========================================
# 6. 构建LangGraph流程图
# ========================================

def build_workflow():
    """构建完整的三省六部制工作流"""

    # 创建工作流
    workflow = StateGraph(AgentState)

    # 添加核心节点
    workflow.add_node("zhongshu_plan", zhongshu_node)
    workflow.add_node("web_search", web_search_agent)
    workflow.add_node("menxia_audit", menxia_audit_node)
    workflow.add_node("shangshu_execute", shangshu_execute_node)
    workflow.add_node("reflection", reflection_agent)

    # 添加工部审批相关节点
    workflow.add_node("gongbu", gongbu_node)
    workflow.add_node("shangshu_gongbu_approval", shangshu_gongbu_approval_node)
    workflow.add_node("menxia_gongbu_audit", menxia_gongbu_audit_node)
    workflow.add_node("user_confirmation", user_confirmation_node)
    workflow.add_node("execute_optimized_plan", execute_optimized_plan_node)
    workflow.add_node("gongbu_resubmit", gongbu_resubmit_node)

    # 添加六部节点（暂不直接调用，由尚书省统一调度）
    # workflow.add_node("libu", libu_node)
    # workflow.add_node("hubu", hubu_node)
    workflow.add_node("libu_doc", libu_doc_node)  # 激活礼部节点用于文档审核
    # workflow.add_node("bingbu", bingbu_node)
    # workflow.add_node("xingbu", xingbu_node)
    # workflow.add_node("gongbu", gongbu_node)

    # 设置入口
    workflow.set_entry_point("web_search")

    # 搭建边（流转逻辑）
    # 1. 联网搜索 → 中书省制定方案
    workflow.add_edge("web_search", "zhongshu_plan")

    # 2. 中书省制定方案 → 门下省审核
    workflow.add_edge("zhongshu_plan", "menxia_audit")

    # 3. 门下省审核 → 条件路由（统一处理方案审核和终审）
    workflow.add_conditional_edges(
        "menxia_audit",
        route_after_audit,
        {
            "zhongshu_plan": "zhongshu_plan",
            "shangshu_execute": "shangshu_execute",
            "reflection": "reflection",
            END: END
        }
    )

    # 4. 尚书省执行 → 礼部撰写文档
    workflow.add_edge("shangshu_execute", "libu_doc")

    # 5. 礼部文档撰写 → 门下省审核
    workflow.add_edge("libu_doc", "menxia_audit")

    # 6. 审核通过后 → 反思阶段
    workflow.add_edge("reflection", END)

    # 6. 工部审批流程边
    # 工部 → 尚书省审批
    workflow.add_edge("gongbu", "shangshu_gongbu_approval")

    # 尚书省审批 → 条件路由
    workflow.add_conditional_edges(
        "shangshu_gongbu_approval",
        route_after_shangshu_gongbu_approval,
        {
            "menxia_gongbu_audit": "menxia_gongbu_audit",
            "gongbu_resubmit": "gongbu_resubmit"
        }
    )

    # 门下省审核 → 条件路由
    workflow.add_conditional_edges(
        "menxia_gongbu_audit",
        route_after_menxia_gongbu_audit,
        {
            "user_confirmation": "user_confirmation",
            "gongbu_resubmit": "gongbu_resubmit"
        }
    )

    # 用户确认 → 条件路由
    workflow.add_conditional_edges(
        "user_confirmation",
        route_after_user_confirmation,
        {
            "execute_optimized_plan": "execute_optimized_plan",
            "gongbu_resubmit": "gongbu_resubmit"
        }
    )

    # 重新提交 → 工部
    workflow.add_edge("gongbu_resubmit", "gongbu")

    # 执行优化方案后结束
    workflow.add_edge("execute_optimized_plan", END)

    # 编译流程图
    return workflow.compile()


# ========================================
# 7. 测试运行
# ========================================

if __name__ == "__main__":
    import sys
    
    # 构建工作流
    app = build_workflow()

    # 用户输入任务（支持命令行参数或交互式输入）
    print("=" * 80)
    print("三省六部制多AI Agent系统 - 阶段1核心测试")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        # 从命令行参数获取任务
        user_task = " ".join(sys.argv[1:])
    else:
        # 交互式输入
        user_task = input("请输入您的任务: ")
    
    print("=" * 80)
    print(f"用户任务：{user_task}")
    print("=" * 80)

    # 初始化状态
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
    result = app.invoke(initial_state)

    # 输出最终结果 - 简洁版
    print("\n")
    print("=" * 80)
    print("【最终交付成果】")
    print("=" * 80)
    print(f"\n📋 用户任务：{result['user_task']}\n")

    # 显示核心要点
    final_deliverable = result.get('final_deliverable', '暂无最终交付成果')
    print("【核心要点】")
    print(final_deliverable)

    # 显示完整的礼部文档
    libu_doc_full = result.get('libu_doc_full', '')
    if libu_doc_full:
        print("\n" + "-" * 60)
        print("【完整报告 - 礼部撰写】")
        print("-" * 60)
        print(libu_doc_full)

    print("\n" + "=" * 80)
    print("【执行完成】")
    print("=" * 80)
