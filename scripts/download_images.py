#!/usr/bin/env python3
"""
从 Markdown 文件下载图床图片并替换为本地路径
用于准备 md 文件转换为 Word 格式

用法：
    python download_images.py <markdown文件路径> [--output-dir <输出目录>]

流程：
1. 解析 markdown 文件中的图片 URL
2. 下载图片到本地目录
3. 将 markdown 中的 URL 替换为本地文件路径
4. 输出修改后的 markdown 文件（用于后续 Word 转换）
"""

import re
import os
import sys
import base64
import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, unquote


def is_local_path(url: str) -> bool:
    """判断是否为本地路径（不需要下载）"""
    return url.startswith('./') or url.startswith('/') or url.startswith('file://')


def download_image(url: str, output_dir: str) -> tuple:
    """
    下载图片到本地
    
    Args:
        url: 图片 URL
        output_dir: 输出目录
    
    Returns:
        tuple: (本地文件路径, 是否成功)
    """
    try:
        # 解析 URL 获取文件名
        parsed = urlparse(url)
        filename = unquote(parsed.path.split('/')[-1])
        
        # 清理文件名
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if not filename or len(filename) > 100:
            # 使用哈希生成文件名
            filename = hashlib.md5(url.encode()).hexdigest()[:12] + '.png'
        
        # 确保有扩展名
        if '.' not in filename:
            filename += '.png'
        
        output_path = os.path.join(output_dir, filename)
        
        # 如果文件已存在，直接返回
        if os.path.exists(output_path):
            return output_path, True
        
        # 下载图片
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            image_data = response.read()
        
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存文件
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return output_path, True
        
    except Exception as e:
        print(f"  ✗ 下载失败 {url}: {e}")
        return None, False


def process_markdown_images(md_content: str, output_dir: str) -> tuple:
    """
    处理 markdown 内容中的图片 URL
    
    Args:
        md_content: markdown 文件内容
        output_dir: 图片输出目录
    
    Returns:
        tuple: (替换后的markdown内容, 下载失败的URL列表)
    """
    # 图片的正则表达式：![alt](url)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    downloaded_paths = {}
    failed_urls = []
    
    def replace_url(match):
        alt_text = match.group(1)
        url = match.group(2).strip()
        
        # 跳过本地路径
        if is_local_path(url):
            return match.group(0)
        
        # 跳过 data:image (base64)
        if url.startswith('data:'):
            return match.group(0)
        
        # 检查是否已下载过
        if url in downloaded_paths:
            local_path = downloaded_paths[url]
            relative_path = f"./images/{os.path.basename(local_path)}"
            return f'![{alt_text}]({relative_path})'
        
        # 下载图片
        print(f"  下载: {url}")
        local_path, success = download_image(url, output_dir)
        
        if success:
            downloaded_paths[url] = local_path
            relative_path = f"./images/{os.path.basename(local_path)}"
            print(f"    ✓ 保存到: {relative_path}")
            return f'![{alt_text}]({relative_path})'
        else:
            failed_urls.append(url)
            return match.group(0)  # 保持原样
    
    # 执行替换
    new_content = re.sub(pattern, replace_url, md_content)
    
    return new_content, failed_urls


def main():
    parser = argparse.ArgumentParser(
        description='从 Markdown 下载图床图片并替换为本地路径'
    )
    parser.add_argument(
        'input_file',
        nargs='?',  # 可选参数
        help='输入的 markdown 文件路径（cleanup 模式下可省略）'
    )
    parser.add_argument(
        '--output-dir',
        '-o',
        help='图片输出目录（默认为 ./images）',
        default=None
    )
    parser.add_argument(
        '--keep-original',
        '-k',
        help='保留原始文件而不是覆盖',
        action='store_true'
    )
    parser.add_argument(
        '--cleanup',
        metavar='目录',
        help='清理指定的图片目录',
        default=None
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file) if args.input_file else None
    
    # 处理 cleanup 模式
    if args.cleanup:
        cleanup_dir = Path(args.cleanup)
        if not cleanup_dir.exists():
            print(f"错误: 目录不存在 - {cleanup_dir}")
            sys.exit(1)
        try:
            import shutil
            shutil.rmtree(cleanup_dir)
            print(f"✓ 已清理临时图片目录: {cleanup_dir}")
            return 0
        except Exception as e:
            print(f"✗ 清理失败: {e}")
            sys.exit(1)
    
    # 非 cleanup 模式需要输入文件
    if not input_path:
        print("错误: 需要提供 markdown 文件路径")
        print("或使用 --cleanup 清理图片目录")
        parser.print_help()
        sys.exit(1)
    
    if not input_path.exists():
        print(f"错误: 文件不存在 - {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.md':
        print(f"警告: 输入文件不是 .md 格式")
    
    # 确定输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent / 'images'
    
    # 读取 markdown 文件
    print(f"读取文件: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有图片 URL
    image_urls = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
    external_urls = [
        url for _, url in image_urls
        if not is_local_path(url) and not url.startswith('data:')
    ]
    
    if not external_urls:
        print("没有发现外部图片 URL，无需处理")
        sys.exit(0)
    
    print(f"发现 {len(external_urls)} 个外部图片")
    print(f"图片将保存到: {output_dir}")
    print()
    
    # 下载图片并替换
    new_content, failed_urls = process_markdown_images(content, str(output_dir))
    
    print()
    
    # 生成输出文件
    if args.keep_original:
        output_path = input_path.parent / f"{input_path.stem}_for_word.md"
    else:
        output_path = input_path.with_suffix('.md')
    
    # 备份原始文件
    if not args.keep_original:
        backup_path = input_path.with_suffix('.md.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已备份原始文件: {backup_path}")
    
    # 写入修改后的 markdown
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 已生成修改后的 markdown: {output_path}")
    print()
    print("后续步骤:")
    print(f"  1. 使用 office-word 或 Pandoc 将 markdown 转换为 Word")
    print(f"  2. Word 转换完成后，清理临时图片:")
    print(f"     python scripts/download_images.py --cleanup {output_dir}")
    
    if failed_urls:
        print()
        print(f"⚠️ 有 {len(failed_urls)} 个图片下载失败，保留原始 URL")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
