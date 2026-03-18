"""
工部审批机制与日志系统测试脚本
"""

from core_architecture import build_workflow, AgentLogger

def test_approval_workflow():
    """测试工部审批工作流"""
    print("=" * 80)
    print("工部审批机制与日志系统测试")
    print("=" * 80)

    # 初始化日志系统
    logger = AgentLogger.get_instance()
    logger.log("测试", "INFO", "开始测试工部审批工作流")

    # 构建工作流
    app = build_workflow()

    # 测试任务
    test_task = "测试工部审批机制：需要技术方案优化"

    print(f"\n测试任务：{test_task}")

    # 初始化状态
    initial_state = {
        "user_task": test_task,
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

    print("\n开始运行工作流...")
    print("-" * 80)

    try:
        # 运行系统
        result = app.invoke(initial_state)

        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)

        # 检查审批流程是否正确
        if 'gongbu_approval_request' in result and result['gongbu_approval_request']:
            print("✅ 工部审批申请已生成")

        if 'optimized_plan' in result and result['optimized_plan']:
            print("✅ 优化方案已生成")

        if 'department_feedback' in result and result['department_feedback']:
            print(f"✅ 已收集 {len(result['department_feedback'])} 个部门的反馈")

        if 'gongbu_approval_status' in result and result['gongbu_approval_status']:
            print(f"✅ 审批状态：{result['gongbu_approval_status']}")

        if 'user_confirmation_result' in result and result['user_confirmation_result']:
            print(f"✅ 用户确认结果：{result['user_confirmation_result']}")

        logger.log("测试", "INFO", "测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")
        logger.log("测试", "ERROR", f"测试失败: {e}")
        raise

if __name__ == "__main__":
    test_approval_workflow()
