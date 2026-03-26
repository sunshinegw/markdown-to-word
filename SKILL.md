# markdown-to-word - Markdown 转 Word 技能

_用于将 Markdown 文件转换为 Word 格式，特别是处理带 base64 内嵌图片的文件。_

## 功能说明

### 1. 提取 base64 图片

Markdown 文件中的 base64 内嵌图片格式：
```markdown
![image_name](data:image/png;base64,/9j/4AAQSkZJRg...)
```

python-docx（Word库）不支持直接读取 base64 内嵌图片，需要先提取为外部文件。

### 2. 转换流程

```
带 base64 图片的 md 文件
        │
        ▼
┌─────────────────────────────┐
│  extract_images.py 脚本      │
│  - 提取 base64 图片          │
│  - 保存为本地 .png/.jpg 文件 │
│  - 替换为外部路径引用         │
└─────────────────────────────┘
        │
        ▼
修改后的 md 文件 + images/ 文件夹
        │
        ▼
┌─────────────────────────────┐
│  office-word       │
│  (MCP 工具)                 │
│  - 创建 Word 文档            │
│  - 引用外部图片              │
└─────────────────────────────┘
        │
        ▼
     Word 文档（含图片）
        │
        ▼
   ⭐ 清理临时图片目录
```

## 使用方法

### 第一步：提取 base64 图片

```bash
python scripts/extract_images.py <markdown文件路径> [选项]
```

**选项：**
- `--output-dir`, `-o`: 指定图片输出目录（默认 `./images`）
- `--keep-original`, `-k`: 保留原始文件，不覆盖
- `--cleanup`: 清理指定的图片目录（用于 Word 完成后删除临时图片）

**示例：**
```bash
# 基本用法
python scripts/extract_images.py 文档.md

# 指定输出目录并保留原文件
python scripts/extract_images.py 文档.md -o ./output --keep-original
```

### 第二步：转换为 Word

使用 office-word MCP 工具：
```
mcporter --config ~/.openclaw/skills/web-tools/config.json call office-word create_document input_file="修改后的.md路径" output_file="输出.docx路径"
```

或使用其他 markdown 转 Word 工具（如 Pandoc）：

```bash
pandoc 输入.md -o 输出.docx --reference-doc=模板.docx
```

### 第三步：清理临时图片 ⭐

Word 转换完成后，清理临时图片目录：
```bash
python3 scripts/extract_images.py --cleanup ./images
```

## 注意事项

- 脚本会自动处理重复的 base64 图片（只提取一次）
- 图片命名：优先使用 alt 文字，否则使用哈希值生成
- 图片保存为 `images/` 子目录
- 生成的 markdown 使用相对路径引用图片（`./images/xxx.png`）

## 目录结构

```
skills/markdown-to-word/
├── SKILL.md                          # 本文件
└── scripts/
    └── extract_images.py            # base64 图片提取脚本
```

## 示例

**原始 markdown (带 base64 图片):**
```markdown
# 文档标题

这是第一张图片：
![截图](data:image/png;base64,iVBORw0KGgo...)

这是第二张图片：
![照片](data:image/jpeg;base64,/9j/4AAQSkZJRg...)
```

**处理后 (外部图片引用):**
```markdown
# 文档标题

这是第一张图片：
![截图](./images/截图.png)

这是第二张图片：
![照片](./images/照片.png)
```

**输出文件结构:**
```
文档.md
文档.md.bak (原始备份)
images/
├── 截图.png
└── 照片.png
```

**Word 转换完成后:**
```bash
python3 scripts/extract_images.py --cleanup ./images
```
