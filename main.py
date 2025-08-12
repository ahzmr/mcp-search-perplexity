#!/usr/bin/env python3
"""
Perplexity MCP Server 启动入口点

使用方法:
    python main.py
    
或者使用 uv:
    uv run main.py
"""

import sys
import asyncio
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from perplexity_mcp.server import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)