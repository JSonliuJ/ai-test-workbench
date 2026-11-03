from mcp.server.fastmcp import FastMCP
import os
import fnmatch
import sys
from pathlib import Path

# 创建 MCP Server
mcp = FastMCP("File_Operations_MCP_Server", host="127.0.0.1", port=9000)

@mcp.tool()
def read_file(file_path: str) -> str:
    """读取指定路径的文件内容
    
    Args:
        file_path: 文件的绝对路径
    
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            return f"文件内容（共 {len(lines)} 行）：\n\n{content}"
    except Exception as e:
        return f"读取文件失败：{str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """将内容写入指定路径的文件
    
    Args:
        file_path: 文件的绝对路径
        content: 要写入的内容
    
    Returns:
        操作结果
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功写入文件：{file_path}"
    except Exception as e:
        return f"写入文件失败：{str(e)}"

@mcp.tool()
def list_directory(dir_path: str, recursive: bool = False) -> str:
    """列出指定目录下的文件和子目录
    
    Args:
        dir_path: 目录的绝对路径
        recursive: 是否递归列出所有子文件
    
    Returns:
        目录内容列表
    """
    try:
        items = []
        
        def scan(current_path, prefix=""):
            try:
                entries = os.listdir(current_path)
                for entry in sorted(entries):
                    full_path = os.path.join(current_path, entry)
                    icon = "📁" if os.path.isdir(full_path) else "📄"
                    items.append(f"{prefix}{icon} {entry}")
                    
                    if os.path.isdir(full_path) and recursive:
                        scan(full_path, prefix + "  ")
            except PermissionError:
                items.append(f"{prefix}⚠️ 无权限访问")
        
        scan(dir_path)
        return f"目录内容：\n\n" + "\n".join(items)
    except Exception as e:
        return f"列出目录失败：{str(e)}"

@mcp.tool()
def search_files(dir_path: str, pattern: str) -> str:
    """在指定目录中搜索匹配的文件
    
    Args:
        dir_path: 搜索的起始目录
        pattern: 搜索模式（支持通配符，如 *.py, *.md）
    
    Returns:
        匹配的文件列表
    """
    try:
        results = []
        
        def scan(current_path):
            try:
                entries = os.listdir(current_path)
                for entry in entries:
                    full_path = os.path.join(current_path, entry)
                    
                    if fnmatch.fnmatch(entry, pattern):
                        results.append(full_path)
                    
                    if os.path.isdir(full_path):
                        scan(full_path)
            except PermissionError:
                pass
        
        scan(dir_path)
        return f"找到 {len(results)} 个匹配文件：\n\n" + "\n".join(results) if results else "找到 0 个匹配文件"
    except Exception as e:
        return f"搜索文件失败：{str(e)}"

@mcp.resource("config://app")
def get_config() -> str:
    """获取应用配置"""
    return """
    应用名称：File Operations MCP Server
    版本：1.0.0
    功能：
    - 读取文件内容
    - 写入文件
    - 列出目录
    - 搜索文件
    """

if __name__ == "__main__":
    # 默认 stdio（供 .mcp.json 的 MCP 客户端使用）；加 --sse 则以 SSE 方式监听 9000 端口
    if "--sse" in sys.argv:
        mcp.run(transport="sse")
    else:
        mcp.run()
    # & ".\.venv\Scripts\python.exe" ".\.claude\FileOperationMcpServer.py"