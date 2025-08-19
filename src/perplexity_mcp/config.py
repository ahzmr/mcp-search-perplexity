#!/usr/bin/env python3
"""
Perplexity MCP 服务器配置管理模块
提供配置加载、验证和管理功能
"""

import os
from typing import Any
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse
import json


@dataclass
class PerplexitySettings:
    """Perplexity 配置设置"""
    api_key: str = ""
    api_url: str = "https://api.perplexity.ai/chat/completions"
    model: str = "sonar"
    model_prefix: str = ""
    system_message: str = "Be precise and concise."
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ProxySettings:
    """代理配置设置"""
    http_proxy: str = ""
    https_proxy: str = ""
    all_proxy: str = ""
    no_proxy: str = ""
    
    def get_proxy_config(self) -> dict[str, str]:
        """获取代理配置字典"""
        proxies: dict[str, str] = {}
        
        # 优先级：具体协议代理 > 通用代理
        if self.http_proxy:
            proxies["http://"] = self.http_proxy
        elif self.all_proxy:
            proxies["http://"] = self.all_proxy
        
        if self.https_proxy:
            proxies["https://"] = self.https_proxy
        elif self.all_proxy:
            proxies["https://"] = self.all_proxy
        
        return proxies
    
    def get_httpx_proxy(self) -> str | None:
        """获取 httpx 客户端使用的单一代理 URL"""
        proxies = self.get_proxy_config()
        if not proxies:
            return None
        
        # 优先使用 HTTPS 代理，如果没有则使用 HTTP 代理
        if "https://" in proxies:
            return proxies["https://"]
        elif "http://" in proxies:
            return proxies["http://"]
        
        return None
    
    def validate_proxy_url(self, proxy_url: str) -> bool:
        """验证代理 URL 格式"""
        try:
            parsed = urlparse(proxy_url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def get_proxy_info(self, proxy_url: str) -> dict[str, str]:
        """获取代理信息（隐藏敏感信息）"""
        try:
            parsed = urlparse(proxy_url)
            info = {
                "scheme": parsed.scheme,
                "host": parsed.hostname or "unknown",
                "port": str(parsed.port) if parsed.port else "default",
            }
            
            if parsed.username:
                info["auth"] = f"{parsed.username}:***"
            
            return info
        except Exception:
            return {"error": "invalid_proxy_url"}


@dataclass
class ServerSettings:
    """服务器配置设置"""
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    log_level: str = "info"
    enable_cors: bool = True
    max_request_size: int = 1024 * 1024  # 1MB


@dataclass
class AppConfig:
    """应用程序完整配置"""
    perplexity: PerplexitySettings
    server: ServerSettings
    proxy: ProxySettings
    debug: bool = False
    config_version: str = "1.0"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str | None = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 config.json
        """
        self.config_file: Path = Path(config_file or "config.json")
        self._config: AppConfig | None = None
    
    def load_config(self) -> AppConfig:
        """
        加载配置，优先级：环境变量 > 配置文件 > 默认值
        
        Returns:
            应用程序配置对象
        """
        # 先加载文件配置
        file_config = self._load_from_file()
        
        # 再加载环境变量配置
        env_config = self._load_from_env()
        
        # 合并配置（环境变量优先）
        config = self._merge_configs(file_config, env_config)
        
        # 验证配置
        self._validate_config(config)
        
        self._config = config
        return config
    
    def _load_from_file(self) -> dict[str, Any]:
        """从文件加载配置"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  警告: 配置文件加载失败: {e}")
            return {}
    
    def _load_from_env(self) -> dict[str, Any]:
        """从环境变量加载配置"""
        env_config: dict[str, Any] = {
            "perplexity": {},
            "server": {},
            "proxy": {},
            "debug": os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
        }
        
        # Perplexity 配置
        perplexity_env = {
            "api_key": os.getenv("PERPLEXITY_API_KEY", ""),
            "api_url": os.getenv("PERPLEXITY_API_URL", ""),
            "model": os.getenv("PERPLEXITY_MODEL", ""),
            "model_prefix": os.getenv("PERPLEXITY_MODEL_PREFIX", ""),
            "system_message": os.getenv("PERPLEXITY_SYSTEM_MESSAGE", ""),
            "timeout": self._parse_float(os.getenv("PERPLEXITY_TIMEOUT")),
            "max_retries": self._parse_int(os.getenv("PERPLEXITY_MAX_RETRIES")),
            "retry_delay": self._parse_float(os.getenv("PERPLEXITY_RETRY_DELAY")),
        }
        
        # 只添加非空的环境变量
        for key, value in perplexity_env.items():
            if value is not None and value != "":
                env_config["perplexity"][key] = value
        
        # 服务器配置
        server_env = {
            "host": os.getenv("MCP_HOST", ""),
            "port": self._parse_int(os.getenv("MCP_PORT")),
            "path": os.getenv("MCP_PATH", ""),
            "log_level": os.getenv("LOG_LEVEL", ""),
            "enable_cors": self._parse_bool(os.getenv("ENABLE_CORS")),
            "max_request_size": self._parse_int(os.getenv("MAX_REQUEST_SIZE")),
        }
        
        for key, value in server_env.items():
            if value is not None and value != "":
                env_config["server"][key] = value
        
        # 代理配置
        proxy_env = {
            "http_proxy": os.getenv("HTTP_PROXY") or os.getenv("http_proxy", ""),
            "https_proxy": os.getenv("HTTPS_PROXY") or os.getenv("https_proxy", ""),
            "all_proxy": os.getenv("ALL_PROXY") or os.getenv("all_proxy", ""),
            "no_proxy": os.getenv("NO_PROXY") or os.getenv("no_proxy", ""),
        }
        
        for key, value in proxy_env.items():
            if value:
                env_config["proxy"][key] = value
        
        return env_config
    
    def _merge_configs(self, file_config: dict[str, Any], env_config: dict[str, Any]) -> AppConfig:
        """合并配置，环境变量优先"""
        # 创建默认配置
        config = AppConfig(
            perplexity=PerplexitySettings(),
            server=ServerSettings(),
            proxy=ProxySettings()
        )
        
        # 应用文件配置
        if "perplexity" in file_config:
            for key, value in file_config["perplexity"].items():
                if hasattr(config.perplexity, key):
                    setattr(config.perplexity, key, value)
        
        if "server" in file_config:
            for key, value in file_config["server"].items():
                if hasattr(config.server, key):
                    setattr(config.server, key, value)
        
        if "debug" in file_config:
            config.debug = file_config["debug"]
        
        # 应用环境变量配置（优先级更高）
        if "perplexity" in env_config:
            for key, value in env_config["perplexity"].items():
                if hasattr(config.perplexity, key):
                    setattr(config.perplexity, key, value)
        
        if "server" in env_config:
            for key, value in env_config["server"].items():
                if hasattr(config.server, key):
                    setattr(config.server, key, value)
        
        if "debug" in env_config:
            config.debug = env_config["debug"]
        
        return config
    
    def _validate_config(self, config: AppConfig) -> None:
        """验证配置"""
        errors: list[str] = []
        
        # 验证 Perplexity 配置
        if not config.perplexity.api_key:
            errors.append("Perplexity API 密钥未设置")
        
        if config.perplexity.timeout <= 0:
            errors.append("超时时间必须大于 0")
        
        if config.perplexity.max_retries < 0:
            errors.append("最大重试次数不能为负数")
        
        # 验证服务器配置
        if not (1 <= config.server.port <= 65535):
            errors.append("端口号必须在 1-65535 范围内")
        
        if config.server.max_request_size <= 0:
            errors.append("最大请求大小必须大于 0")
        
        if errors:
            print("⚠️  配置验证警告:")
            for error in errors:
                print(f"   - {error}")
    
    def save_config(self, config: AppConfig | None = None) -> None:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置，默认使用当前配置
        """
        if config is None:
            config = self._config
        
        if config is None:
            raise ValueError("没有可保存的配置")
        
        config_dict = {
            "perplexity": asdict(config.perplexity),
            "server": asdict(config.server),
            "debug": config.debug,
            "config_version": config.config_version
        }
        
        # 创建配置目录
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存到: {self.config_file}")
        except IOError as e:
            print(f"❌ 配置保存失败: {e}")
            raise
    
    def create_sample_config(self) -> None:
        """创建示例配置文件"""
        sample_config = AppConfig(
            perplexity=PerplexitySettings(
                api_key="your-perplexity-api-key-here",
                api_url="https://api.perplexity.ai/chat/completions",
                model="sonar",
                model_prefix="",
                system_message="Be precise and concise. Provide accurate information.",
                timeout=30.0,
                max_retries=3,
                retry_delay=1.0
            ),
            server=ServerSettings(
                host="127.0.0.1",
                port=8000,
                path="/mcp",
                log_level="info",
                enable_cors=True,
                max_request_size=1024 * 1024
            ),
            proxy=ProxySettings(),
            debug=False,
            config_version="1.0"
        )
        
        config_dict = {
            "_comment": "Perplexity MCP 服务器配置文件",
            "_description": {
                "perplexity.api_key": "Perplexity API 密钥 (必需)",
                "perplexity.api_url": "Perplexity API 端点URL",
                "perplexity.model": "使用的模型名称",
                "perplexity.model_prefix": "模型名称前缀，会自动添加到模型名称前面",
                "perplexity.system_message": "默认系统消息",
                "perplexity.timeout": "请求超时时间（秒）",
                "server.host": "服务器绑定地址",
                "server.port": "服务器端口",
                "server.path": "MCP 端点路径"
            },
            "perplexity": asdict(sample_config.perplexity),
            "server": asdict(sample_config.server),
            "debug": sample_config.debug,
            "config_version": sample_config.config_version
        }
        
        sample_file = Path("config.sample.json")
        try:
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"✅ 示例配置文件已创建: {sample_file}")
        except IOError as e:
            print(f"❌ 示例配置文件创建失败: {e}")
    
    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        """解析整数值"""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        """解析浮点数值"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None
    
    @staticmethod
    def _parse_bool(value: str | None) -> bool | None:
        """解析布尔值"""
        if value is None or value == "":
            return None
        return value.lower() in ("true", "1", "yes", "on")
    
    def get_config(self) -> AppConfig | None:
        """获取当前配置"""
        return self._config
    
    def print_config_status(self) -> None:
        """打印配置状态"""
        if self._config is None:
            print("❌ 配置未加载")
            return
        
        config = self._config
        
        print("📋 当前配置状态:")
        print(f"   🔑 API 密钥: {'已设置' if config.perplexity.api_key else '❌ 未设置'}")
        print(f"   🌐 API URL: {config.perplexity.api_url}")
        print(f"   🤖 模型: {config.perplexity.model}")
        print(f"   🏷️  模型前缀: {config.perplexity.model_prefix if config.perplexity.model_prefix else '未设置'}")
        print(f"   💬 系统消息: {config.perplexity.system_message[:50]}{'...' if len(config.perplexity.system_message) > 50 else ''}")
        print(f"   ⏱️  超时时间: {config.perplexity.timeout}秒")
        print(f"   🔄 最大重试: {config.perplexity.max_retries}次")
        print(f"   🌐 服务器: {config.server.host}:{config.server.port}{config.server.path}")
        print(f"   📊 日志级别: {config.server.log_level}")
        print(f"   🐛 调试模式: {'开启' if config.debug else '关闭'}")


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """获取全局配置"""
    config = config_manager.get_config()
    if config is None:
        config = config_manager.load_config()
    return config


def load_config_from_file(config_file: str) -> AppConfig:
    """从指定文件加载配置"""
    manager = ConfigManager(config_file)
    return manager.load_config()


if __name__ == "__main__":
    """命令行配置管理工具"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python config.py load          - 加载并显示配置")
        print("  python config.py create-sample - 创建示例配置文件")
        print("  python config.py save          - 保存当前配置")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "load":
        config = config_manager.load_config()
        config_manager.print_config_status()
    
    elif command == "create-sample":
        config_manager.create_sample_config()
    
    elif command == "save":
        try:
            config = config_manager.load_config()
            config_manager.save_config(config)
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            sys.exit(1)
    
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)