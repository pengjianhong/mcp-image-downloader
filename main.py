from mcp.server.fastmcp import FastMCP
import os
import requests
import logging
import mimetypes
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("mcp-image-downloader")

@mcp.tool()
def download_image(url, save_dir, filename) -> str:
    """下载图片
    Args:
        url: 图片URL
        save_dir: 保存目录
        filename: 保存文件名
    Returns:
        str: 成功时返回保存路径，失败时返回失败原因
    """
    import datetime
    
    # 检查URL是否有效
    if not url or not url.startswith(('http://', 'https://')):
        return "无效的URL"
    
    # 创建保存目录
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        return f"创建目录失败: {str(e)}"
    
    # 处理文件名和扩展名
    if not filename:
        filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    # 从URL中获取文件扩展名
    url_path = urlparse(url).path
    ext = os.path.splitext(url_path)[1]
    
    # 如果文件名中没有扩展名，则添加
    if not os.path.splitext(filename)[1]:
        filename = filename + (ext if ext else '.jpg')  # 默认使用.jpg
    
    save_path = os.path.join(save_dir, filename)
    
    try:
        # 设置流式请求和超时
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 检查内容类型是否为图片
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith(('image/', 'application/octet-stream')):
            return f"下载失败: 非图片类型 ({content_type})"
        
        # 使用内容类型更新扩展名（如果URL中没有提供）
        if not ext and 'image/' in content_type:
            new_ext = mimetypes.guess_extension(content_type)
            if new_ext and not filename.endswith(new_ext):
                filename = os.path.splitext(filename)[0] + new_ext
                save_path = os.path.join(save_dir, filename)
        
        # 限制文件大小 (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_size = int(response.headers.get('Content-Length', 0))
        if file_size > max_size:
            return f"下载失败: 文件大小 ({file_size / 1024 / 1024:.2f}MB) 超过限制 (10MB)"
        
        # 下载文件
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"图片已保存至 {save_path}")
        return save_path
        
    except requests.exceptions.RequestException as e:
        error_msg = f"下载失败: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')
