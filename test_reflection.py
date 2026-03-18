"""
快速测试反思功能
"""

from core_architecture import build_workflow

# 构建工作流
app = build_workflow()

# 简化的初始状态
initial_state = {
    "user_task": "写一个Hello World函数",
    "loop_count": 0,
    "audit_status": "pending",
    "execution_stage": "plan",
    "messages": [],
    "zhongshu_plan": "",
    "menxia_audit_result": "",
    "shangshu_result": "",
    "liubo_results": {},
    "reflection_report": ""
}

print("开始测试反思功能...")

try:
    # 运行系统
    result = app.invoke(initial_state)

    print("测试完成！")
    print(f"反思报告长度: {len(result.get('reflection_report', ''))}")
    if result.get('reflection_report'):
        print("反思报告预览:")
        print(result['reflection_report'][:200] + "...")
    else:
        print("未找到反思报告")

except Exception as e:
    print(f"测试失败: {e}")