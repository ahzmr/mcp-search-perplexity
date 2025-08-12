# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 FastMCP 的 Streamable-HTTP MCP 服务器，提供 Perplexity AI 搜索功能。它将原本的 JavaScript Perplexity 搜索功能转换为支持 Streamable-HTTP 传输协议的 MCP 服务。

## 开发命令

### 安装和设置
```bash
# 安装依赖
pip install -r requirements.txt
# 或使用 uv（推荐）
uv pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件并设置您的 Perplexity API 密钥
```

### 运行服务器
```bash
# 启动服务器
python main.py

# 或使用 uv
uv run main.py
```

### 测试
```bash
# 运行完整测试套件
python tests/test_client.py

# 运行简单/快速测试
python tests/test_client.py simple

# 交互式测试模式
python tests/test_client.py interactive
```

### 配置管理
```bash
# 加载并显示当前配置
python src/perplexity_mcp/config.py load

# 创建示例配置文件
python src/perplexity_mcp/config.py create-sample

# 保存当前配置到文件
python src/perplexity_mcp/config.py save
```

## 架构设计

### 核心组件

- **`main.py`**: 入口点，将 src/ 添加到 Python 路径并启动服务器
- **`src/perplexity_mcp/server.py`**: 主要的 FastMCP 服务器实现，包含：
  - Perplexity AI API 集成
  - 代理支持配置
  - HTTP 客户端管理
  - 错误处理和日志记录
- **`src/perplexity_mcp/config.py`**: 配置管理系统，包含：
  - 环境变量和文件配置
  - 配置验证和合并
  - 基于数据类的设置结构
- **`tests/test_client.py`**: 全面的服务器功能测试套件

### 主要功能

- **Perplexity AI 搜索**: 单一工具 `search`，参数：
  - `keyword` (必需): 搜索查询
  - `model` (可选): 模型选择 (sonar, sonar-pro...)
  - `system_message` (可选): 自定义系统提示
- **代理支持**: 从环境变量自动配置代理 (HTTP_PROXY, HTTPS_PROXY, ALL_PROXY)
- **Streamable-HTTP 传输**: 使用 FastMCP 进行基于 HTTP 的 MCP 通信
- **全面错误处理**: API 超时、代理错误、身份验证失败
- **引用支持**: 保留和格式化 Perplexity 的引用信息

### 配置

配置优先级: 环境变量 > 配置文件 > 默认值

关键环境变量：
- `PERPLEXITY_API_KEY`: 搜索功能必需
- `PERPLEXITY_MODEL`: 默认模型 (默认: "sonar")
- `PERPLEXITY_SYSTEM_MESSAGE`: 默认系统提示
- `PERPLEXITY_TIMEOUT`: 请求超时时间，秒 (默认: 30.0)
- `MCP_HOST`, `MCP_PORT`, `MCP_PATH`: 服务器绑定配置
- 代理变量: `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`

### 服务器端点

- 服务器默认运行在 `http://127.0.0.1:8000/mcp`
- 使用 FastMCP 的 Streamable-HTTP 传输协议
- 包含用于请求/响应调试的日志中间件

## 开发说明

- 需要 Python 3.13+（在 pyproject.toml 中指定）
- 使用 FastMCP 2.9.0+ 框架实现 MCP 协议
- 主要依赖: fastmcp, httpx 用于异步 HTTP 操作
- 测试依赖: pytest, pytest-asyncio
- 所有服务器功能完全异步
- 整个代码库和文档支持中文

## MCP 开发最佳实践参考

### 详细实践指南

参考 `../mcp-python-docs/mcp-development-best-practices.md` 获取完整的 MCP 开发最佳实践，包含：
- 标准项目结构规范（src-layout布局）
- 工具开发模式和错误处理
- 配置管理层级（环境变量 > 配置文件 > 默认值）
- 企业级代理支持实现
- 全面的测试策略（连接、工具、资源、错误处理测试）
- 中间件使用和自定义开发
- 质量检查清单和故障排除指南

### FastMCP Streamable-HTTP 指南

参考 `../mcp-python-docs/fastmcp-guide.md` 了解 FastMCP 框架详细用法，包含：
- Streamable-HTTP 传输协议配置
- 与 FastAPI/Starlette 集成方案
- 认证机制（Bearer Token等）
- 内置中间件使用（日志、计时、重试）
- 完整的实际示例和最佳实践
- 常见问题排除和调试技巧