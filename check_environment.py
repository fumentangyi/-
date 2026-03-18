"""
环境检查脚本
快速验证所有依赖是否就绪
"""
import sys
import subprocess

def check_python_version():
    """检查Python版本"""
    print("=" * 60)
    print("检查Python版本")
    print("=" * 60)
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print("[OK] Python版本符合要求（3.8+）")
        return True
    else:
        print("[ERROR] Python版本不符合要求，需要3.8+")
        return False

def check_packages():
    """检查必需的Python包"""
    print("\n" + "=" * 60)
    print("检查必需的Python包")
    print("=" * 60)

    required_packages = [
        "langchain",
        "langgraph", 
        "langchain_ollama",
        "streamlit",
        "requests",
        "beautifulsoup4"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"✗ {package} 未安装")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n缺少的包: {', '.join(missing_packages)}")
        print("安装命令: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✓ 所有必需的包都已安装")
        return True

def check_ollama():
    """检查Ollama是否可用"""
    print("\n" + "=" * 60)
    print("检查Ollama服务")
    print("=" * 60)

    try:
        # 检查ollama命令是否可用
        result = subprocess.run(['ollama', '--version'],
                              capture_output=True,
                              text=True,
                              timeout=5)

        if result.returncode == 0:
            print(f"✓ Ollama已安装: {result.stdout.strip()}")

            # 检查已下载的模型
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)

            if result.returncode == 0:
                print("\n已安装的模型:")
                print(result.stdout)

                if "qwen2:7b" in result.stdout:
                    print("✓ qwen2:7b模型已下载")
                    return True
                else:
                    print("✗ qwen2:7b模型未下载")
                    print("下载命令: ollama pull qwen2:7b")
                    return False
            else:
                print("✗ 无法获取模型列表")
                return False
        else:
            print("✗ Ollama命令不可用")
            print("请从 https://ollama.com 下载安装Ollama")
            return False

    except subprocess.TimeoutExpired:
        print("✗ Ollama命令执行超时")
        return False
    except FileNotFoundError:
        print("✗ Ollama未安装")
        print("请从 https://ollama.com 下载安装Ollama")
        return False
    except Exception as e:
        print(f"✗ 检查Ollama时出错: {e}")
        return False

def test_ollama_connection():
    """测试Ollama连接"""
    print("\n" + "=" * 60)
    print("测试Ollama连接")
    print("=" * 60)

    try:
        from langchain_ollama import OllamaLLM

        print("正在测试模型连接...")
        llm = OllamaLLM(model="qwen2:7b", temperature=0.3)

        print("发送测试请求...")
        response = llm.invoke("你好，请回复'连接成功'")
        print(f"✓ 模型响应: {response}")

        if "连接" in response or "成功" in response:
            print("\n✓ Ollama连接测试成功")
            return True
        else:
            print("\n⚠️ 模型响应不符合预期，但连接正常")
            return True

    except Exception as e:
        print(f"✗ Ollama连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("三省六部制多AI Agent系统 - 环境检查")
    print("=" * 60)

    results = []

    # 运行各项检查
    results.append(("Python版本", check_python_version()))
    results.append(("Python包", check_packages()))
    results.append(("Ollama安装", check_ollama()))

    # 只有前面的检查都通过，才测试连接
    if all(result for _, result in results):
        results.append(("Ollama连接", test_ollama_connection()))

    # 输出总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)

    all_passed = all(result for _, result in results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有检查通过！可以运行核心架构测试了")
        print("运行命令: venv\\Scripts\\python.exe core_architecture.py")
    else:
        print("\n⚠️ 还有问题需要解决，请根据上面的提示处理")

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
