# 基于mineru的 PDF 转换与翻译工具

## 项目简介

本项目基于mineru实现，提供一个**高效、灵活的 PDF 文档处理流水线**。它从输入的 PDF 文件开始，利用 mineru（一个强大的 PDF 内容解析和结构化工具）将其精确地转换为结构化的 Markdown 格式。在此基础上，项目支持可选的自动翻译功能，以满足多语言处理的需求。最终，处理后的 Markdown 文档可以被高质量地渲染回 PDF 文件，特别强调了对 LaTeX 数学公式（通过 MathJax 渲染）以及图片、表格的完美呈现。

本工具不仅提供了**灵活的命令行接口**，允许用户通过脚本批量处理文档，还特别设计了一个**直观的 Web 用户界面**。这个 Web 界面使得非技术用户也能轻松上传文件、配置处理参数（例如跳过翻译或保留中间文件），并实时查看处理进度和最终结果的 PDF 预览。无论是自动化工作流还是即时处理单个文件，本项目都能提供便捷高效的解决方案。

## 功能特性

*   **PDF 到 Markdown 转换**：利用 `magic_pdf` 库，将输入的 PDF 文件精确地转换为 Markdown 格式，同时智能地提取并管理文档中的图片。
*   **Markdown 翻译**：支持对生成的 Markdown 文件进行翻译（目前默认使用百度翻译 API，您可以在 `src/config.py` 中配置您的 API 凭证及源语言/目标语言）。
*   **Markdown 到 PDF 转换**：将 Markdown 文件转换为高质量的 PDF，**特别支持 MathJax 渲染 LaTeX 数学公式**，确保科学和技术文档的准确呈现。
*   **Web 用户界面 (Gradio)**：提供基于 Gradio 的直观 Web 界面，通过简单的文件上传和参数选择即可执行整个流程，无需命令行经验。
*   **PDF 实时预览**：在 Web 界面中提供生成的 PDF 文档的实时多页预览功能，支持滚动查看。
*   **中间文件控制**：支持通过命令行参数或 Web 界面选项，选择是否保留转换过程中生成的中间文件（如原始 Markdown、翻译后的 Markdown 和临时 HTML 文件），便于调试和进一步处理。
*   **一键式操作**：命令行工具和 Web 界面均支持一键执行完整流程，简化操作步骤。

## 安装

1.  **克隆项目**：
    ```bash
    git clone <项目仓库地址> # 如果您有git仓库，请替换为您的仓库地址
    cd <项目根目录>
    ```
    如果您没有 Git 仓库，请确保您当前的工作目录就是项目根目录。

2.  **配置mineru环境**
    具体请到：https://github.com/opendatalab/MinerU

3.  **安装 Python 依赖**：
    ```bash
    pip install -r requirements.txt
    ```

4.  **安装 wkhtmltopdf（项目已包含）**：
    `wkhtmltopdf` 是用于将 HTML 转换为 PDF 的外部工具。
    *   **下载**：访问 [wkhtmltopdf 官方网站](https://wkhtmltopdf.org/downloads.html) 下载适用于您操作系统的版本。
    *   **安装**：按照安装向导进行安装。
    *   **配置路径 (可选)**：通常安装程序会自动将其添加到系统 PATH。如果未添加到 PATH，您需要确保 `wkhtmltopdf.exe` (Windows) 或 `wkhtmltopdf` (Linux/macOS) 位于项目的 `wkhtmltopdf/bin/` 目录下，或者在调用时通过 `--wkpath` 参数指定其完整路径。

5.  **配置百度翻译 API (可选)**：
    如果您需要使用翻译功能，请编辑 `src/config.py` 文件，填入您的百度翻译 API 的 APP ID 和密钥。
    ```python
    # src/config.py
    BAIDU_TRANSLATE_APP_ID = "您的APP ID"
    BAIDU_TRANSLATE_APP_KEY = "您的密钥"
    ```

## 使用方法

### 1. 命令行使用

在项目根目录下，您可以直接运行 `main.py` 来执行转换流程。

```bash
python main.py <输入的PDF文件路径> [选项]
```

**示例：**

*   **将 `test3.pdf` 转换为 Markdown，然后翻译并生成 PDF (默认行为)：**
    ```bash
    python main.py test3.pdf
    ```
    生成的 PDF 将位于 `output/test3.pdf`，中间文件将被删除。

*   **将 `test3.pdf` 转换为 Markdown 并生成 PDF，跳过翻译步骤：**
    ```bash
    python main.py test3.pdf --skip-translation
    ```

*   **将 `test3.pdf` 转换为 Markdown，翻译并生成 PDF，并保留所有中间文件：**
    ```bash
    python main.py test3.pdf --keep-intermediate
    ```

*   **指定输出目录和输出文件名：**
    ```bash
    python main.py test3.pdf -o my_output/translated_doc.pdf
    ```

### 2. Web 界面使用

在项目根目录下运行 `app.py` 来启动 Web 服务：

```bash
python app.py
```

服务启动后，您的默认浏览器会自动打开一个新标签页，显示 Web 界面。如果浏览器没有自动打开，请手动访问终端中显示的本地 URL (通常是 `http://127.0.0.1:7860`)。

**Web 界面操作：**

1.  **上传 PDF 文件**：点击“上传PDF文件”区域，选择您的 PDF 文件。
2.  **选择参数**：
    *   `跳过翻译步骤`：勾选此项将跳过 Markdown 翻译。
    *   `保留中间文件 (.md, .html)`：勾选此项将在 `output` 目录中保留所有中间文件。
3.  **开始处理**：点击“开始处理”按钮。
4.  **查看日志和预览**：处理日志会实时显示在“处理日志”文本框中。处理完成后，“PDF 预览”区域将显示生成的 PDF 文件，您可以通过滚动来翻页。
5.  **下载 PDF**：处理完成后，“下载生成的PDF”区域会出现下载链接，点击即可下载最终的 PDF 文件。
6.  **关闭服务**：如果您想停止 Web 服务，点击“关闭服务”按钮即可。

**项目结构**
.
├── main.py # 命令行入口，协调整个流程
├── app.py # Gradio Web 应用入口
├── requirements.txt # Python 依赖列表
├── wkhtmltopdf/ # wkhtmltopdf 可执行文件存放目录 (可选，如果添加到系统PATH可省略)
│ └── bin/
│ └── wkhtmltopdf.exe # 或其他操作系统对应的可执行文件
├── output/ # 默认输出目录，包含生成的PDF、Markdown和临时HTML文件
│ └── previews/ # 预览图片存放目录
├── src/ # 核心代码目录
│ ├── init.py # 标记 src 为 Python 包
│ ├── pdf_to_markdown.py # 将PDF转换为Markdown的逻辑
│ ├── translate_markdown.py # Markdown翻译逻辑
│ ├── markdown_to_pdf.py # 将Markdown转换为PDF的逻辑 (支持MathJax)
│ ├── translation_api.py # 翻译API抽象和百度翻译实现
│ ├── markdown_translator.py # Markdown内容翻译器
│ └── config.py # 项目配置，如百度翻译API密钥、语言设置
└── README.md # 项目说明文件