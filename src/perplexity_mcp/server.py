#!/usr/bin/env python3
"""
Perplexity MCP Server
基于 FastMCP 的 Streamable-HTTP MCP 服务器，提供 Perplexity AI 搜索功能
"""

from typing import Any
from pathlib import Path
from fastmcp import FastMCP, Context
from fastmcp.server.middleware.logging import LoggingMiddleware
import httpx
from .config import get_config

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    # 查找 .env 文件
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        _ = load_dotenv(env_file)
        print(f"✅ 已加载环境变量文件: {env_file}")
    else:
        print(f"⚠️  .env 文件不存在: {env_file}")
except ImportError:
    print("⚠️  python-dotenv 未安装，跳过 .env 文件加载")


# 创建 FastMCP 服务器实例
mcp = FastMCP("Perplexity Search MCP Server")

# 添加日志中间件
mcp.add_middleware(LoggingMiddleware(
    include_payloads=True,
    max_payload_length=500
))

# 加载配置
config = get_config()


def parse_proxy_config() -> dict[str, str]:
    """解析代理配置"""
    return config.proxy.get_proxy_config()


def validate_proxy_url(proxy_url: str) -> bool:
    """验证代理 URL 格式"""
    return config.proxy.validate_proxy_url(proxy_url)


def get_proxy_info(proxy_url: str) -> dict[str, str]:
    """获取代理信息（隐藏敏感信息）"""
    return config.proxy.get_proxy_info(proxy_url)


async def create_http_client() -> httpx.AsyncClient:
    """创建配置了代理的 HTTP 客户端"""
    # 创建客户端配置
    client_config: dict[str, Any] = {
        "timeout": config.perplexity.timeout,
        "follow_redirects": True,
    }
    
    # 获取代理配置
    proxy_url = config.proxy.get_httpx_proxy()
    
    if proxy_url and validate_proxy_url(proxy_url):
        client_config["proxy"] = proxy_url
        proxy_info = get_proxy_info(proxy_url)
        print("🌐 使用代理配置:")
        print(f"   代理: {proxy_info.get('scheme')}://{proxy_info.get('host')}:{proxy_info.get('port')}")
        if "auth" in proxy_info:
            print(f"   认证: {proxy_info['auth']}")
    elif proxy_url:
        print(f"⚠️  警告: 代理 URL 格式无效: {proxy_url}")
        print("🔗 直接连接（代理配置无效）")
    else:
        print("🔗 直接连接（未配置代理）")
    
    return httpx.AsyncClient(**client_config)


@mcp.tool
async def search(
    keyword: str,
    model: str | None = config.perplexity.model,
    system_message: str | None = config.perplexity.system_message,
    ctx: Context | None = None
) -> str:
    """
    使用 Perplexity AI 从互联网搜索信息。
    
    Args:
        keyword: 搜索关键词或问题，支持自然语言查询
        model: 模型名称（可选）。支持的模型包括：
            - sonar: 标准搜索模型，平衡速度和质量
            - sonar-pro: 专业搜索模型，提供更深入的分析
            - sonar-reasoning: 推理增强模型，适合复杂问题
            - sonar-reasoning-pro: 专业推理模型，最高质量的分析
            - sonar-deep-research: 深度研究模型，适合学术和研究查询
            默认使用配置文件中设置的模型
        system_message: 系统提示信息（可选），用于指导AI的回答风格和格式
            默认："Be precise and concise."
    
    Returns:
        搜索结果文本，包含相关信息和引用来源
        
    Examples:
        - search("最新的人工智能发展趋势")
        - search("Python异步编程最佳实践", model="sonar-pro")
        - search("气候变化对农业的影响", model="sonar-deep-research", system_message="请提供详细的科学分析")
    """
    if ctx:
        await ctx.info(f"开始使用 Perplexity 搜索: {keyword}")
    
    # 验证 API 密钥
    if not config.perplexity.api_key:
        error_msg = "请在配置文件或环境变量 PERPLEXITY_API_KEY 中设置 Perplexity API 密钥"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    # 使用传入的参数或默认配置
    used_model = model or config.perplexity.model
    # 如果配置了模型前缀，自动添加到模型名称前面
    if config.perplexity.model_prefix and not used_model.startswith(config.perplexity.model_prefix):
        used_model = config.perplexity.model_prefix + used_model
    used_system_message = system_message or config.perplexity.system_message
    
    if ctx:
        await ctx.info(f"使用模型: {used_model}")
        await ctx.debug(f"系统消息: {used_system_message}")
    
    # 准备请求数据
    request_data = {
        "model": used_model,
        "messages": [
            {
                "role": "system",
                "content": used_system_message
            },
            {
                "role": "user",
                "content": keyword
            }
        ]
    }
    
    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {config.perplexity.api_key}"
    }
    
    try:
        if ctx:
            await ctx.info("正在调用 Perplexity API...")
        
        # 发送请求
        client = await create_http_client()
        async with client:
            response = await client.post(
                config.perplexity.api_url,
                headers=headers,
                json=request_data
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"Perplexity API 请求失败: {response.status_code} - {response.text}"
                if ctx:
                    await ctx.error(error_msg)
                raise httpx.HTTPStatusError(error_msg, request=response.request, response=response)
            
            # 解析响应
            response_data: dict[str, Any] = response.json()
            
            if ctx:
                await ctx.debug(f"API 响应状态: {response.status_code}")
            
        # 处理响应数据
        if "choices" not in response_data:
            error_msg = "Perplexity API 响应格式无效：缺少 choices 字段"
            if ctx:
                await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        # 提取内容
        choices = response_data.get("choices", [])
        if not choices:
            if ctx:
                await ctx.warning("API 返回了空的 choices")
            return "未找到搜索结果"
        
        # 合并所有选择的内容
        content_parts: list[str] = []
        for choice in choices:
            if "message" in choice and "content" in choice["message"]:
                content_parts.append(choice["message"]["content"])
        
        content = " ".join(content_parts)
        
        # 处理引用信息
        citations = response_data.get("citations", [])
        result = content
        
        if citations:
            if ctx:
                await ctx.info(f"找到 {len(citations)} 个引用")
            
            citations_text = "\n\n引用信息:\n"
            for index, citation in enumerate(citations, 1):
                citations_text += f"[{index}] {citation}\n"
            
            result += citations_text
        
        if ctx:
            await ctx.info(f"搜索完成，返回 {len(content)} 个字符的结果")
        
        return result
    
    except httpx.TimeoutException:
        error_msg = f"Perplexity API 请求超时（{config.perplexity.timeout}秒）"
        if ctx:
            await ctx.error(error_msg)
            proxies = parse_proxy_config()
            if proxies:
                await ctx.error("如果使用代理，请检查代理配置和网络连接")
        raise TimeoutError(error_msg)
    
    except httpx.ProxyError as e:
        error_msg = f"代理连接错误: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
            await ctx.error("请检查代理配置是否正确，或尝试禁用代理")
        raise ConnectionError(error_msg)
    
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP 请求错误: {e.response.status_code} - {e.response.text}"
        if ctx:
            await ctx.error(error_msg)
        raise
    
    except Exception as e:
        error_msg = f"未预期的错误: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise


def main():
    """主函数 - 运行 MCP 服务器"""
    print("🚀 启动 Perplexity MCP 服务器...")
    
    # 检查基础配置
    if not config.perplexity.api_key:
        print("⚠️  警告: 未设置 PERPLEXITY_API_KEY")
        print("   请在配置文件或环境变量中设置后再使用搜索功能")
    else:
        print("✅ Perplexity API 密钥已配置")
    
    print(f"📊 当前配置:")
    print(f"   模型: {config.perplexity.model}")
    print(f"   系统消息: {config.perplexity.system_message}")
    print(f"   超时时间: {config.perplexity.timeout}秒")
    print(f"   最大重试次数: {config.perplexity.max_retries}")
    print(f"   重试延迟: {config.perplexity.retry_delay}秒")
    
    # 检查代理配置（同步版本）
    proxies = parse_proxy_config()
    if proxies:
        print(f"\n🌐 代理配置检测:")
        for protocol, proxy_url in proxies.items():
            proxy_info = get_proxy_info(proxy_url)
            print(f"   {protocol} -> {proxy_info.get('scheme')}://{proxy_info.get('host')}:{proxy_info.get('port')}")
    else:
        print("\n🔗 未配置代理，将直接连接")
    
    print("\n" + "="*50)
    
    print(f"🚀 服务器配置: {config.server.host}:{config.server.port}{config.server.path}")
    print(f"📊 日志级别: {config.server.log_level}")
    
    # 运行服务器
    mcp.run(
        transport="http",  # 使用 Streamable-HTTP
        host=config.server.host,
        port=config.server.port,
        path=config.server.path,
        log_level=config.server.log_level
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")