"""
短期记忆管理模块
负责：记忆的添加、查询、摘要、注射
"""

from typing import List, Dict, Optional
import datetime

def get_timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")


class MemoryManager:
    """短期记忆管理器 - 负责单个任务周期内的记忆管理"""

    def __init__(self, max_memory: int = 50):
        self.memories: List[Dict] = []
        self.max_memory = max_memory
        self.importance_threshold = 2

    def add_memory(self,
                   content: str,
                   stage: str,
                   source: str,
                   importance: int = 3,
                   key_points: Optional[List[str]] = None) -> None:
        """添加一条记忆"""
        memory_item = {
            "timestamp": get_timestamp(),
            "stage": stage,
            "source": source,
            "content": content,
            "importance": importance,
            "key_points": key_points or []
        }
        self.memories.append(memory_item)

        if len(self.memories) > self.max_memory:
            self.memories.sort(key=lambda x: (x["importance"], x["timestamp"]))
            self.memories = self.memories[-self.max_memory:]

    def get_memory_context(self,
                          query_type: str = "all",
                          top_k: int = 5) -> str:
        """获取与当前操作相关的记忆上下文"""
        filtered = self.memories
        if query_type != "all":
            filtered = [m for m in filtered if m["stage"] == query_type]

        if not filtered:
            return "（当前无相关记忆）"

        filtered.sort(key=lambda x: x["importance"], reverse=True)
        filtered = filtered[:top_k]

        context = "【本轮任务记忆参考】\n"
        for i, memory in enumerate(filtered, 1):
            context += f"{i}. [{memory['timestamp']}] {memory['source']}: {memory['content']}\n"
            if memory['key_points']:
                context += f"   └─ 关键点: {', '.join(memory['key_points'])}\n"
        return context

    def generate_memory_summary(self) -> str:
        """生成本阶段的记忆摘要"""
        if not self.memories:
            return "【记忆摘要】暂无记忆"

        by_stage = {"decision": [], "audit": [], "execution": []}
        for m in self.memories:
            stage = m["stage"]
            if stage in by_stage:
                by_stage[stage].append(m)

        summary = "【本轮记忆摘要】\n"

        for stage_name, stage_label in [("decision", "决策"), ("audit", "审核"), ("execution", "执行")]:
            items = by_stage[stage_name]
            if items:
                summary += f"\n✓ {stage_label}阶段({len(items)}条):\n"
                for item in sorted(items, key=lambda x: x["importance"], reverse=True)[:2]:
                    summary += f"  • {item['content'][:60]}{'...' if len(item['content']) > 60 else ''}\n"

        return summary

    def clear_memory(self) -> None:
        """清除所有记忆"""
        self.memories.clear()

    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        return {
            "total_memories": len(self.memories),
            "by_stage": {
                "decision": len([m for m in self.memories if m["stage"] == "decision"]),
                "audit": len([m for m in self.memories if m["stage"] == "audit"]),
                "execution": len([m for m in self.memories if m["stage"] == "execution"])
            },
            "avg_importance": sum(m["importance"] for m in self.memories) / len(self.memories) if self.memories else 0
        }

    def extract_key_points(self, text: str, max_points: int = 3) -> List[str]:
        """从文本中提取关键点"""
        sentences = text.split('。')
        key_points = []
        for sent in sentences[:max_points]:
            sent = sent.strip()
            if len(sent) > 5:
                key_points.append(sent[:50])
        return key_points


memory_manager: Optional[MemoryManager] = None


def init_memory_manager() -> MemoryManager:
    """初始化全局记忆管理器"""
    global memory_manager
    memory_manager = MemoryManager()
    return memory_manager


def get_memory_manager() -> MemoryManager:
    """获取全局记忆管理器"""
    global memory_manager
    if memory_manager is None:
        memory_manager = init_memory_manager()
    return memory_manager