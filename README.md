# 基于minerU的 PDF 转换、翻译与预览工具

## 简介

本项目是一个基于minerU的高效、灵活的 PDF 文档处理流水线。它能将输入的 PDF 文件精确地转换为结构化的 Markdown，支持可选的自动翻译，并最终将 Markdown 高质量地渲染回 PDF 格式。

本工具的核心优势在于**对复杂内容的高保真处理**，包括对 LaTeX 数学公式（通过 MathJax 渲染）、图片和表格的完美支持。

为了满足不同用户的需求，项目同时提供了两种操作模式：
*   **命令行接口 (CLI)**：方便开发者和高级用户进行脚本化和批量处理。
*   **Web 用户界面 (Web UI)**：通过直观的图形界面，让普通用户也能轻松上传文件、配置参数、实时预览并下载结果。

---

## 功能特性

*   **PDF 到 Markdown**：利用 minerU，精确地将 PDF 转换为结构化 Markdown，并自动提取图片。
*   **自动翻译**：集成百度翻译 API，可对 Markdown 文本进行自动翻译。
*   **Markdown 到 PDF**：将 Markdown 渲染为高质量 PDF，特别强化了对 MathJax 公式的支持。
*   **Web UI**：基于 Gradio 构建，提供文件上传、参数配置、日志显示、实时预览和结果下载等全套功能。
*   **实时预览**：在 Web 界面中可即时预览上传的原始 PDF 和处理后的结果 PDF，支持滚动和缩放。
*   **灵活控制**：无论是命令行还是 Web 界面，都支持跳过翻译、保留中间文件等选项，便于调试和自定义。

---


## 项目结构

```
.
├── src/                    # 核心源代码
│   ├── __init__.py
│   ├── config.py           # API 密钥和语言配置
│   ├── markdown_to_pdf.py  # Markdown 转 PDF 模块
│   ├── markdown_translator.py # Markdown 翻译逻辑
│   ├── pdf_to_markdown.py  # PDF 转 Markdown 模块
│   └── translation_api.py  # 翻译 API 接口
├── wkhtmltopdf/            # wkhtmltopdf 可执行程序
├── app.py                  # Web UI (Gradio) 启动文件
├── main.py                 # 命令行 (CLI) 启动文件
├── requirements.txt        # Python 依赖
└── README.md               # 项目说明文档
```

---

## 安装与配置

1.  **克隆项目**
    ```bash
    git clone https://github.com/Ae486/pdfTranslator
    cd pdfTranslator
    ```

2.  **配置 MinerU 环境 (必需)**
    本项目依赖 MinerU 进行核心的 PDF 解析。请务必先按照其官方指南完成环境配置。
    *   **详细指南**: [https://github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)

3.  **安装 Python 依赖**
    建议在虚拟环境中安装，以避免与系统库冲突。
    ```bash
    pip install -r requirements.txt
    ```
    *（`wkhtmltopdf` 已包含在项目中，无需额外安装。）*

4.  **配置百度翻译 API (可选)**
    如果需要使用翻译功能，请编辑 `src/config.py` 文件，填入您的百度翻译 API 的 APP ID 和密钥。
    ```python
    # src/config.py
    BAIDU_TRANSLATE_APP_ID = "您的APP ID"
    BAIDU_TRANSLATE_APP_KEY = "您的密钥"
    ```

---

## 使用方法

### 方式一：Web 界面 (推荐)

在项目根目录下运行 `app.py` 启动 Web 服务。

```bash
python app.py
```
服务启动后，您的默认浏览器将自动打开 Web 界面。如果未能自动打开，请手动访问终端中显示的本地 URL (通常是 `http://127.0.0.1:7860`)。

**操作流程：**
1.  **上传文件**：在左侧上传您的 PDF 文件，预览区会立即显示原始文件。
2.  **配置选项**：根据需要勾选"跳过翻译步骤"或"保留中间文件"。
3.  **开始处理**：点击"开始处理"按钮。
4.  **查看结果**：
    *   右侧日志区会实时显示处理步骤。
    *   处理完成后，预览区会自动切换到显示最终生成的 PDF。您也可以通过上方的"原文件"/"翻译结果"按钮随时切换预览内容。
    *   最下方的下载区域会提供最终 PDF 文件的下载链接。

### 方式二：命令行

在项目根目录下，通过运行 `main.py` 使用命令行工具。

```bash
python main.py <输入的PDF文件路径> [选项]
```

**常用示例：**

*   **默认完整流程** (转换 -> 翻译 -> 生成PDF)
    ```bash
    python main.py assets/test3.pdf
    ```
    *结果将保存在 `output/` 目录，中间文件会被自动删除。*

*   **跳过翻译步骤**
    ```bash
    python main.py assets/test3.pdf --skip-translation
    ```

*   **保留所有中间文件** (如 `.md`, `.html`)
    ```bash
    python main.py assets/test3.pdf --keep-intermediate
    ```

*   **指定输出目录**
    ```bash
    python main.py assets/test3.pdf -o my_output/
    ```
