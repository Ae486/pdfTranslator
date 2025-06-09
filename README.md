# PDF转Markdown工具

这是一个专门用于将PDF文件转换为Markdown格式的工具，基于magic_pdf库开发。

## 功能特点

- 支持文本型PDF和OCR型PDF自动识别和处理
- 提取PDF中的图片，保存到指定目录
- 提供命令行和Web界面两种使用方式
- 保留原PDF中的文本结构和格式
- 简单易用，转换速度快

## 安装

1. 确保已安装Python 3.7或更高版本
2. 克隆或下载本项目
3. 安装依赖:

```bash
pip install -r requirements.txt
```

4. 确保magic_pdf库已正确安装配置

## 使用方法

### 命令行方式

```bash
python pdf_to_markdown.py /path/to/your/document.pdf -o /output/directory
```

### Web服务方式

启动Web服务:

```bash
python pdf_markdown_api.py
```

然后在浏览器中访问 http://localhost:5000 使用Web界面上传和转换PDF。

### API调用方式

可以通过HTTP请求调用API:

```python
import requests

url = "http://localhost:5000/api/convert"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
result = response.json()
print(result)
```

## 输出结果

成功转换后会生成:

- `{文件名}.md` - Markdown文件
- `images/` - 包含所有提取的图片

## 注意事项

- 对于大型PDF文件，转换可能需要较长时间
- 复杂排版的PDF可能无法完美转换所有格式
- 确保有足够的磁盘空间存储转换后的文件和图片

## 许可

本项目采用MIT许可证。 