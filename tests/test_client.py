#!/usr/bin/env python3
"""
Perplexity MCP 服务器客户端测试脚本
用于测试 Streamable-HTTP MCP 服务器的所有功能
"""

import asyncio
import json
from typing import Dict, Any
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


class MCPClientTester:
    """MCP 客户端测试器"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8000/mcp"):
        """
        初始化测试客户端
        
        Args:
            server_url: MCP 服务器 URL
        """
        self.server_url = server_url
        self.transport = StreamableHttpTransport(url=server_url)
    
    async def test_connection(self) -> bool:
        """测试服务器连接"""
        print("🔗 测试服务器连接...")
        
        try:
            async with Client(self.transport) as client:
                await client.ping()
                print("✅ 连接成功")
                return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def test_list_tools(self) -> bool:
        """测试获取工具列表"""
        print("\n🛠️  测试获取工具列表...")
        
        try:
            async with Client(self.transport) as client:
                tools = await client.list_tools()
                print(f"✅ 获取到 {len(tools)} 个工具:")
                
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description}")
                    
                    # 显示参数
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        properties = tool.inputSchema.get('properties', {})
                        if properties:
                            print(f"     参数: {', '.join(properties.keys())}")
                
                return len(tools) > 0
                
        except Exception as e:
            print(f"❌ 获取工具列表失败: {e}")
            return False
    
    async def test_list_resources(self) -> bool:
        """测试获取资源列表"""
        print("\n📚 测试获取资源列表...")
        
        try:
            async with Client(self.transport) as client:
                resources = await client.list_resources()
                print(f"✅ 获取到 {len(resources)} 个资源:")
                
                for resource in resources:
                    print(f"   - {resource.uri}: {resource.name}")
                    if hasattr(resource, 'description') and resource.description:
                        print(f"     {resource.description}")
                
                return len(resources) >= 0  # 现在没有资源也算正常
                
        except Exception as e:
            print(f"❌ 获取资源列表失败: {e}")
            return False
    

    async def test_search_functionality(self) -> bool:
        """测试搜索功能（需要有效的 API 密钥）"""
        print("\n🔍 测试搜索功能...")
        
        test_queries = [
            "Python 异步编程基本概念",
            "机器学习入门指南",
            "现在几点了"
        ]
        
        success_count = 0
        
        try:
            async with Client(self.transport) as client:
                for query in test_queries:
                    try:
                        print(f"   搜索: {query}")
                        result = await client.call_tool("search", {
                            "keyword": query
                        })
                        
                        if result.data:
                            response_text = result.data
                            print(f"   ✅ 搜索成功，结果长度: {len(response_text)}")
                            
                            # 显示搜索结果的前100个字符
                            preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
                            print(f"   结果预览: {preview}")
                            
                            # 检查是否包含引用
                            if "引用信息:" in response_text or "Citations:" in response_text:
                                print("   📚 包含引用信息")
                            
                            success_count += 1
                        else:
                            print(f"   ⚠️  搜索结果为空")
                            
                    except Exception as e:
                        print(f"   ❌ 搜索 '{query}' 失败: {e}")
                        
                        # 检查是否是 API 密钥问题
                        if "API Key" in str(e) or "api_key" in str(e):
                            print("   💡 提示: 请设置 PERPLEXITY_API_KEY 环境变量")
                
                return success_count > 0
                
        except Exception as e:
            print(f"❌ 搜索功能测试失败: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理"""
        print("\n🚨 测试错误处理...")
        
        try:
            async with Client(self.transport) as client:
                # 测试无效工具调用
                try:
                    await client.call_tool("nonexistent_tool", {})
                    print("   ❌ 应该抛出错误但没有")
                    return False
                except Exception:
                    print("   ✅ 无效工具调用正确处理")
                
                # 测试无效参数
                try:
                    await client.call_tool("search", {})  # 缺少必需参数
                    print("   ❌ 应该抛出参数错误但没有")
                    return False
                except Exception:
                    print("   ✅ 无效参数正确处理")
                
                return True
                
        except Exception as e:
            print(f"❌ 错误处理测试失败: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🧪 开始运行 Perplexity MCP 服务器测试套件\n")
        print("=" * 60)
        
        tests = [
            ("连接测试", self.test_connection),
            ("工具列表", self.test_list_tools),
            ("资源列表", self.test_list_resources),
            ("错误处理", self.test_error_handling),
            ("搜索功能", self.test_search_functionality),  # 放在最后，因为需要 API 密钥
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ 测试 {test_name} 发生异常: {e}")
                results[test_name] = False
        
        # 显示测试结果摘要
        print("\n" + "=" * 60)
        print("📊 测试结果摘要:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🏆 总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！")
        elif passed >= total * 0.7:
            print("👍 大部分测试通过，服务器基本功能正常")
        else:
            print("⚠️  有多个测试失败，请检查服务器配置")
        
        return results


async def run_simple_test():
    """运行简单的快速测试"""
    print("🚀 运行快速测试...")
    
    tester = MCPClientTester()
    
    # 只测试基本连接和工具列表
    connection_ok = await tester.test_connection()
    if connection_ok:
        await tester.test_list_tools()
        await tester.test_list_resources()
    
    return connection_ok


async def run_interactive_test():
    """运行交互式测试"""
    print("🎮 交互式测试模式")
    print("您可以手动输入搜索查询来测试服务器")
    
    tester = MCPClientTester()
    
    # 检查连接
    if not await tester.test_connection():
        print("❌ 无法连接到服务器，退出交互模式")
        return
    
    try:
        async with Client(tester.transport) as client:
            while True:
                query = input("\n输入搜索查询 (输入 'quit' 退出): ").strip()
                
                if query.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 退出交互模式")
                    break
                
                if not query:
                    continue
                
                try:
                    print(f"🔍 搜索: {query}")
                    result = await client.call_tool("search", {
                        "keyword": query
                    })
                    
                    print(f"\n📋 搜索结果:")
                    print("-" * 50)
                    print(result.data)
                    print("-" * 50)
                    
                except Exception as e:
                    print(f"❌ 搜索失败: {e}")
                    
                    if "API Key" in str(e) or "api_key" in str(e):
                        print("💡 提示: 请设置 PERPLEXITY_API_KEY 环境变量")
                
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出交互模式")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode in ['simple', 's']:
            print("🏃‍♂️ 运行简单测试...")
            asyncio.run(run_simple_test())
        
        elif mode in ['interactive', 'i']:
            asyncio.run(run_interactive_test())
        
        elif mode in ['help', 'h']:
            print("用法:")
            print("  python test_client.py [mode]")
            print("")
            print("模式:")
            print("  simple, s      - 运行简单的快速测试")
            print("  interactive, i - 运行交互式测试")
            print("  full (默认)    - 运行完整测试套件")
            print("  help, h        - 显示此帮助")
        
        else:
            print(f"❌ 未知模式: {mode}")
            print("使用 'python test_client.py help' 查看帮助")
            sys.exit(1)
    
    else:
        # 默认运行完整测试
        print("🧪 运行完整测试套件...")
        tester = MCPClientTester()
        asyncio.run(tester.run_all_tests())