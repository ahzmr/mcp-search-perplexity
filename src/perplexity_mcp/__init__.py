"""
Perplexity MCP Server Package

基于 FastMCP 的 Streamable-HTTP MCP 服务器，提供 Perplexity AI 搜索功能
"""

__version__ = "1.0.0"
__author__ = "MCP Team"
__description__ = "Perplexity AI search MCP server with HTTP proxy support"

from .server import main

__all__ = ["main"]