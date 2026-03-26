#!/usr/bin/env python3
"""
从 Markdown 文件中提取 base64 内嵌图片并转换为外部文件引用
用于准备 md 文件转换为 Word 格式

用法：
    python extract_images.py <markdown文件路径> [--output-dir <输出目录>]

流程：
1. 解析 markdown 文件中的 base64 图片
2. 解码并保存为本地图片文件
3. 将 markdown 中的 base64 引用替换为本地文件路径
4. 输出修改后的 markdown 文件（用于后续 Word 转换）
"""

import re
import os
import sys
import base64
import argparse
from pathlib import Path
from urllib.parse import unquote


def extract_base64_images(md_content, output_dir, md_filename):
    """
    从 markdown 内容中提取 base64 图片并保存为本地文件
    
    Args:
        md_content: markdown 文件内容
        output_dir: 图片输出目录
        md_filename: 原始 markdown 文件名（用于生成图片文件名）
    
    Returns:
        tuple: (替换后的markdown内容, 提取的图片路径列表)
    """
    # base64 图片的正则表达式
    # 匹配 ![name](data:image/png;base64,...) 或 ![name](data:image/jpeg;base64,...)
    pattern = r'!\[([^\]]*)\]\(data:([a-zA-Z]+)/([a-zA-Z\-]+);base64,([^\)]+)\)'
    
    # 用于存储已提取的图片（避免重复）
    extracted_images = {}
    
    def replace_base64_image(match):
        alt_text = match.group(1)  # 图片名称/alt文字
        mime_type = match.group(2)  # image/png 或 image/jpeg
        mime_subtype = match.group(3)  # png, jpeg, gif等
        base64_data = match.group(4)  # base64 编码的数据
        
        # 生成唯一的图片文件名
        # 标准化 mime_subtype：jpeg -> jpg（避免 .jpeg 双扩展）
        ext = 'jpg' if mime_subtype.lower() == 'jpeg' else mime_subtype.lower()
        
        if alt_text:
            # 使用 alt 文字作为文件名
            safe_name = re.sub(r'[^\w\s\-\.]', '', alt_text)[:50]  # 保留前50字符，移除非安全字符
            # 避免重复添加扩展名（检查各种可能的扩展名变体）
            alt_lower = safe_name.lower()
            if alt_lower.endswith(f'.{ext}') or alt_lower.endswith('.jpeg'):
                image_name = safe_name
            else:
                image_name = f"{safe_name}.{ext}"
        else:
            # 使用哈希值生成唯一名称
            image_hash = hash(base64_data[:100]) % 100000
            image_name = f"image_{image_hash}.{ext}"
        
        image_path = os.path.join(output_dir, image_name)
        
        # 避免重复提取相同的 base64 数据
        if image_name not in extracted_images:
            try:
                # 解码 base64 数据
                image_data = base64.b64decode(base64_data)
                
                # 确保目录存在
                os.makedirs(output_dir, exist_ok=True)
                
                # 保存图片文件
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                extracted_images[image_name] = image_path
                print(f"  ✓ 提取图片: {image_name} ({len(image_data)} bytes)")
                
            except Exception as e:
                print(f"  ✗ 提取图片失败 {image_name}: {e}")
                return match.group(0)  # 保持原样
        
        # 返回替换后的 markdown 引用（使用相对路径）
        relative_path = f"./images/{image_name}"
        return f'![{alt_text}]({relative_path})'
    
    # 执行替换
    new_content = re.sub(pattern, replace_base64_image, md_content)
    
    return new_content, list(extracted_images.values())


def main():
    parser = argparse.ArgumentParser(
        description='从 Markdown 文件提取 base64 内嵌图片并转换为外部文件引用'
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
        help='清理指定的图片目录（用于 Word 转换完成后删除临时图片）',
        default=None
    )
    
    args = parser.parse_args()
    
    # 验证输入文件
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
        # 默认为输入文件同目录下的 images 文件夹
        output_dir = input_path.parent / 'images'
    
    # 确保输出目录的 images 子文件夹存在
    images_dir = output_dir
    
    # 读取 markdown 文件
    print(f"读取文件: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有 base64 图片
    base64_count = len(re.findall(r'data:[a-zA-Z]+/[a-zA-Z\-]+;base64,', content))
    if base64_count == 0:
        print("没有发现 base64 内嵌图片，无需处理")
        sys.exit(0)
    
    print(f"发现 {base64_count} 个 base64 内嵌图片")
    print(f"图片将保存到: {images_dir}")
    print()
    
    # 提取图片并替换
    new_content, extracted_paths = extract_base64_images(content, str(images_dir), input_path.stem)
    
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
    print(f"  - 提取了 {len(extracted_paths)} 个图片到: {images_dir}")
    print()
    print("后续步骤:")
    print(f"  1. 使用 office-word 将 markdown 转换为 Word")
    print(f"  2. Word 转换完成后，清理临时图片:")
    print(f"     python3 scripts/extract_images.py --cleanup {images_dir}")
    
    return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
