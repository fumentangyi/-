"""
测试联网搜索功能
"""

from core_architecture import perform_web_search

# 测试搜索功能
if __name__ == "__main__":
    print("测试联网搜索功能...")

    # 测试关键词
    keywords = "人工智能发展趋势"

    try:
        results = perform_web_search(keywords)
        print(f"搜索到 {len(results)} 条结果")

        for i, result in enumerate(results[:3], 1):  # 只显示前3条
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   摘要: {result['snippet'][:100]}...")

    except Exception as e:
        print(f"搜索测试失败: {e}")