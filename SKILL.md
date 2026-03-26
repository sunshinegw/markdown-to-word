# markdown-to-word - Markdown 转 Word 技能

_用于将 Markdown 文件转换为 Word 格式。图片从图床下载到本地，转换完成后清理临时文件。_

## 功能说明

Markdown 文件中的图片通常使用图床 URL 引用：
```markdown
![截图](http://192.168.1.100:5000/Picture/abc123.png)
```

Word 文档需要本地图片文件，本脚本负责：
1. 下载图床图片到本地
2. 替换 Markdown 中的 URL 为本地路径
3. 转换为 Word 后清理临时文件

## 转换流程

```
Markdown 文件（图床 URL）
        │
        ▼
┌─────────────────────────────┐
│  download_images.py 脚本     │
│  - 下载图片到本地目录         │
│  - 替换 URL 为本地路径        │
└─────────────────────────────┘
        │
        ▼
修改后的 md 文件 + images/ 文件夹
        │
        ▼
┌─────────────────────────────┐
│  office-word (MCP 工具)     │
│  - 创建 Word 文档            │
│  - 引用本地图片              │
└─────────────────────────────┘
        │
        ▼
     Word 文档（含图片）
        │
        ▼
   ⭐ 清理临时图片目录
```

## 使用方法

### 第一步：下载图床图片

```bash
python scripts/download_images.py <markdown文件路径> [选项]
```

**选项：**
- `--output-dir`, `-o`: 指定图片输出目录（默认 `./images`）
- `--keep-original`, `-k`: 保留原始文件，不覆盖
- `--cleanup`: 清理指定的图片目录

**示例：**
```bash
# 基本用法
python scripts/download_images.py 文档.md

# 指定输出目录
python scripts/download_images.py 文档.md -o ./output

# 清理临时图片
python scripts/download_images.py --cleanup ./images
```

### 第二步：转换为 Word

使用 office-word MCP 工具：
```
/openclaw mcporter call office-word create_document input_file="文档.md" output_file="文档.docx"
```

或使用 Pandoc：
```bash
pandoc 文档.md -o 文档.docx
```

### 第三步：清理临时图片 ⭐

Word 转换完成后清理：
```bash
python scripts/download_images.py --cleanup ./images
```

## 支持的图片格式

| 格式 | 示例 URL |
|------|----------|
| Dufs 图床 | `http://192.168.1.100:5000/Picture/xxx.png` |
| SM.MS | `https://i.loli.net/xxx.jpg` |
| 其他 URL | 任何可直接下载的图片 URL |

## 注意事项

- 支持 http/https URL
- 自动跳过本地路径图片（`./`、`/` 开头）
- 自动跳过非图片 URL
- 图片命名：优先使用 URL 中的文件名，否则使用哈希值
- 自动处理重复图片（相同 URL 只下载一次）

## 目录结构

```
skills/markdown-to-word/
├── SKILL.md                          # 本文件
└── scripts/
    └── download_images.py            # 图片下载脚本
```

## 示例

**原始 markdown (图床 URL):**
```markdown
# 产品介绍

![产品图](http://192.168.1.100:5000/Picture/产品图.png)

这是功能说明。
```

**处理后 (本地路径):**
```markdown
# 产品介绍

![产品图](./images/产品图.png)

这是功能说明。
```

**输出文件结构:**
```
文档.md
文档.md.bak (原始备份)
images/
└── 产品图.png
```

**Word 转换完成后:**
```bash
python scripts/download_images.py --cleanup ./images
```
