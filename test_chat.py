# 导入对接Ollama的工具
from langchain_ollama import OllamaLLM

# 初始化本地大模型，如果你用的是qwen2:3b，就把括号里的改成"qwen2:3b"
llm = OllamaLLM(model="qwen2:7b", temperature=0.3)

# 让模型说话，打印结果
response = llm.invoke("你好，我是大学生，正在从零做AI Agent，你能给我打个气吗？")
print("AI回复：", response)
