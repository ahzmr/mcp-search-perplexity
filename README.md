# Perplexity MCP Server

> 基于 FastMCP 的 Streamable-HTTP MCP 服务器，提供 Perplexity AI 搜索功能

## 概述

这是一个使用 Python FastMCP 框架开发的 MCP (Model Context Protocol) 服务器，它将原本的 JavaScript Perplexity 搜索功能转换为了支持 Streamable-HTTP 传输协议的 MCP 服务。

### 主要特性

- 🔍 **Perplexity AI 搜索**: 使用 Perplexity AI 从互联网搜索信息
- 🌐 **Streamable-HTTP**: 基于现代 HTTP 传输协议
- ⚡ **异步处理**: 完全异步的请求处理
- 🔧 **配置灵活**: 支持环境变量和配置文件
- 📊 **内置日志**: 详细的请求和错误日志
- 🛡️ **错误处理**: 完善的错误处理和验证
- 🎯 **引用支持**: 保留 Perplexity 的引用信息

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或者使用 uv
uv pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置您的 Perplexity API 密钥
export PERPLEXITY_API_KEY="your-api-key-here"
```

### 3. 启动服务器

```bash
python main.py
```

服务器将在 `http://127.0.0.1:8000/mcp` 启动。

### 4. 测试服务器

```bash
# 运行完整测试套件
python tests/test_client.py

# 运行简单测试
python tests/test_client.py simple

# 交互式测试
python tests/test_client.py interactive
```

## 功能说明

### 工具 (Tools)

#### `search`
使用 Perplexity AI 从互联网搜索信息。支持 HTTP/HTTPS/SOCKS 代理配置。支持多种模型：sonar（标准）、sonar-pro（专业）、codellama-34b-instruct（编程）、llama-2-70b-chat（通用对话）。

**参数:**
- `keyword` (必需): 搜索关键词
- `model` (可选): 模型名称（默认：sonar）
- `system_message` (可选): 系统提示信息（默认：Be precise and concise.）

**示例:**
```json
{
  "keyword": "Python 异步编程最佳实践",
  "model": "sonar-pro",
  "system_message": "请提供详细的技术信息"
}
```

## 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `PERPLEXITY_API_KEY` | Perplexity API 密钥 | - | ✅ |
| `PERPLEXITY_MODEL` | 默认模型 | `sonar` | ❌ |
| `PERPLEXITY_SYSTEM_MESSAGE` | 默认系统消息 | `Be precise and concise.` | ❌ |
| `PERPLEXITY_TIMEOUT` | 请求超时时间(秒) | `30.0` | ❌ |
| `HTTP_PROXY` | HTTP 代理地址 | - | ❌ |
| `HTTPS_PROXY` | HTTPS 代理地址 | - | ❌ |
| `ALL_PROXY` | 通用代理地址 | - | ❌ |
| `MCP_HOST` | 服务器绑定地址 | `127.0.0.1` | ❌ |
| `MCP_PORT` | 服务器端口 | `8000` | ❌ |
| `MCP_PATH` | MCP 端点路径 | `/mcp` | ❌ |
| `LOG_LEVEL` | 日志级别 | `info` | ❌ |

### 支持的模型

- `sonar`: 标准搜索模型，平衡准确性和速度
- `sonar-pro`: 专业搜索模型，更高准确性

## 客户端连接

### Python 客户端示例

```python
import asyncio
from fastmcp import Client

async def search_example():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        # 搜索信息
        result = await client.call_tool("search", {
            "keyword": "最新的人工智能发展趋势"
        })
        
        print(result.text)

asyncio.run(search_example())
```

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "perplexity-search": {
      "url": "http://127.0.0.1:8000/mcp",
      "transport": "http"
    }
  }
}
```

## 开发指南

### 项目结构

```
mcp-search-ppl/
├── main.py                     # 主启动文件
├── config.py                   # 配置管理
├── requirements.txt            # 依赖文件
├── .env.example               # 环境变量示例
├── README.md                  # 项目说明
└── tests/
    └── test_client.py         # 测试客户端
```

### 自定义开发

1. **添加新工具**: 在 `main.py` 中使用 `@mcp.tool` 装饰器
2. **添加新资源**: 使用 `@mcp.resource` 装饰器
3. **修改配置**: 编辑 `config.py` 中的配置类
4. **添加中间件**: 使用 `mcp.add_middleware()` 添加自定义中间件

### 测试和调试

```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=debug

# 运行服务器
python main.py

# 运行测试
python tests/test_client.py
```

## 故障排除

### 常见问题

#### 1. 连接失败
```bash
❌ 连接失败: Connection refused
```
**解决方案**: 确保服务器正在运行，检查 host 和 port 配置。

#### 2. API 密钥错误
```bash
❌ 请在环境变量 PERPLEXITY_API_KEY 中设置 Perplexity API 密钥
```
**解决方案**: 设置正确的 Perplexity API 密钥。

#### 3. 搜索超时
```bash
❌ Perplexity API 请求超时（30.0秒）
```
**解决方案**: 增加 `PERPLEXITY_TIMEOUT` 环境变量的值。

### 日志调试

启用详细日志来诊断问题：

```bash
export LOG_LEVEL=debug
export DEBUG=true
python main.py
```

## 部署

### 本地部署

```bash
# 启动服务器
python main.py
```

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
```

### 生产环境

```bash
# 使用 Gunicorn 部署
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:mcp.http_app()
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[MIT License](LICENSE)

## 相关资源

- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [Perplexity AI API](https://docs.perplexity.ai/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [Claude Desktop MCP](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)