import os
import sys
import argparse
import re
import markdown
import subprocess
import shutil
import time  # 添加time模块导入
from typing import Optional
import html
import pdfkit


#    - \tiny    : 极小字体
#    - \scriptsize : 脚本字体
#    - \small   : 小字体
#    - \normalsize : 正常字体
#    - \large   : 大字体
#    - \Large   : 更大字体
#    - \LARGE   : 很大字体
#    - \huge    : 巨大字体
#    - \Huge    : 极巨大字体


def preprocess_math_tags_for_mathjax(content):
    """预处理Markdown中的数学公式标签，将HTML标签替换为原始的LaTeX形式"""
    
    # 处理特殊的HTML实体和标签
    def decode_html_entities(match):
        content = match.group(1)
        # 解码HTML实体
        decoded = html.unescape(content)
        # 移除HTML标签
        no_tags = re.sub(r'<.*?>', '', decoded)
        return f"${no_tags}$"
    
    # 处理更复杂的行内公式
    def handle_complex_inline_math(match):
        content = match.group(1)
        # 解码HTML实体
        decoded = html.unescape(content)
        # 移除HTML标签，但保留内容
        no_tags = re.sub(r'<[^>]*>', '', decoded)
        # 为行内公式增加大型显示标记 \normalsize
        return f"$\\normalsize {no_tags}$"
    
    # 处理块级公式，添加 \normalsize 指令
    def handle_block_math(match):
        content = match.group(1)
        return f"$$\\normalsize {content}$$"
    
    # 替换行内公式 <span class="math-inline">$formula$</span> -> $\normalsize formula$
    inline_pattern = r'<span class="math-inline">\$(.*?)\$</span>'
    content = re.sub(inline_pattern, handle_complex_inline_math, content)
    
    # 替换块级公式 <div class="math-block">$$formula$$</div> -> $$\normalsize formula$$
    block_pattern = r'<div class="math-block">\$\$(.*?)\$\$</div>'
    content = re.sub(block_pattern, handle_block_math, content)
    
    # 手动替换一些特殊情况，避免使用复杂的正则表达式
    content = content.replace('{o<em>{1}', '{o_{1}')
    content = content.replace('{o<em>{2}', '{o_{2}')
    content = content.replace('$\\mathrm{RL}<em>{\\cdot}$', '$\\large \\mathrm{RL}_{\\cdot}$')
    
    # 其他常见的LaTeX修复
    content = content.replace('\\pi_{\\theta_{o l d}}', '\\pi_{\\theta_{old}}')
    content = content.replace('\\scriptstyle{\\pi_{\\theta}}', '\\scriptstyle{\\pi_{\\theta}}')
    
    return content

def fix_image_paths(html_content, source_file_dir, output_dir):
    """修复HTML中的图片路径，确保在PDF生成时能找到图片"""
    
    # 创建临时图片目录
    temp_images_dir = os.path.join(output_dir, 'images')
    os.makedirs(temp_images_dir, exist_ok=True)
    
    # 查找所有图片标签，包括Markdown格式转换后的img标签和原始的![](path)格式
    img_pattern = r'<img[^>]*src="([^"]*)"[^>]*>'
    img_matches = list(re.finditer(img_pattern, html_content))
    
    # 还要查找markdown中的图片格式: ![](images/xxx.jpg) - 这些可能需要直接替换
    md_img_pattern = r'!\[(.*?)\]\(([^)]+)\)'
    md_img_matches = list(re.finditer(md_img_pattern, html_content))
    
    replaced_html = html_content
    
    # 处理HTML img标签
    for match in img_matches:
        full_match = match.group(0)
        img_src = match.group(1)
        
        # 跳过已经是绝对路径的图片
        if img_src.startswith('http://') or img_src.startswith('https://'):
            continue
            
        # 处理相对路径，无论是images/xxx.jpg还是直接xxx.jpg
        img_filename = os.path.basename(img_src)
        
        # 检查不同可能的源图片路径
        possible_paths = [
            img_src,  # 直接路径
            os.path.join(source_file_dir, img_src),  # 源文件目录下的路径
            os.path.join(source_file_dir, 'images', img_filename),  # 源文件目录下的images子目录
            os.path.join(os.path.dirname(source_file_dir), 'image', img_filename),  # 上级目录的image子目录
            os.path.join(os.getcwd(), 'image', img_filename),  # 当前工作目录的image子目录
            os.path.join(os.getcwd(), 'images', img_filename),  # 当前工作目录的images子目录
        ]
        
        # 查找存在的图片路径
        source_img_path = None
        for path in possible_paths:
            if os.path.exists(path):
                source_img_path = path
                break
                
        if source_img_path:
            # 目标路径为输出目录下的images子目录
            target_img_path = os.path.join(temp_images_dir, img_filename)
            # 复制图片文件，添加异常处理和重试逻辑
            for retry in range(3):  # 最多尝试3次
                try:
                    shutil.copy2(source_img_path, target_img_path)
                    print(f"已复制图片: {source_img_path} -> {target_img_path}")
                    break  # 成功复制就跳出循环
                except PermissionError as e:
                    print(f"警告: 文件被占用，等待重试 ({retry+1}/3): {e}")
                    if retry < 2:  # 如果不是最后一次尝试
                        time.sleep(1)  # 等待1秒
                    else:
                        print(f"错误: 无法复制图片 {source_img_path}，跳过")
                except Exception as e:
                    print(f"错误: 复制图片失败: {e}")
                    break  # 其他错误直接跳出
            
            # 替换原来的路径为临时目录中的路径
            new_src = f'images/{img_filename}'
            new_img_tag = full_match.replace(img_src, new_src)
            replaced_html = replaced_html.replace(full_match, new_img_tag)
        else:
            print(f"警告: 找不到图片: {img_src}")
            
    # 处理Markdown格式图片
    for match in md_img_matches:
        full_match = match.group(0)
        alt_text = match.group(1)
        img_src = match.group(2)
        
        # 跳过已经是绝对路径的图片
        if img_src.startswith('http://') or img_src.startswith('https://'):
            continue
            
        img_filename = os.path.basename(img_src)
        
        # 检查不同可能的源图片路径
        possible_paths = [
            img_src,  # 直接路径
            os.path.join(source_file_dir, img_src),  # 源文件目录下的路径
            os.path.join(source_file_dir, 'images', img_filename),  # 源文件目录下的images子目录
            os.path.join(os.path.dirname(source_file_dir), 'image', img_filename),  # 上级目录的image子目录
            os.path.join(os.getcwd(), 'image', img_filename),  # 当前工作目录的image子目录
            os.path.join(os.getcwd(), 'images', img_filename),  # 当前工作目录的images子目录
        ]
        
        # 查找存在的图片路径
        source_img_path = None
        for path in possible_paths:
            if os.path.exists(path):
                source_img_path = path
                break
                
        if source_img_path:
            # 目标路径为输出目录下的images子目录
            target_img_path = os.path.join(temp_images_dir, img_filename)
            # 复制图片文件
            if not os.path.exists(target_img_path):
                for retry in range(3):  # 最多尝试3次
                    try:
                        shutil.copy2(source_img_path, target_img_path)
                        print(f"已复制图片: {source_img_path} -> {target_img_path}")
                        break  # 成功复制就跳出循环
                    except PermissionError as e:
                        print(f"警告: 文件被占用，等待重试 ({retry+1}/3): {e}")
                        if retry < 2:  # 如果不是最后一次尝试
                            time.sleep(1)  # 等待1秒
                        else:
                            print(f"错误: 无法复制图片 {source_img_path}，跳过")
                    except Exception as e:
                        print(f"错误: 复制图片失败: {e}")
                        break  # 其他错误直接跳出
            
            # 替换为HTML图片标签
            new_img_tag = f'<img src="images/{img_filename}" alt="{alt_text}" />'
            replaced_html = replaced_html.replace(full_match, new_img_tag)
        else:
            print(f"警告: 找不到图片: {img_src}")
            
    return replaced_html

def markdown_to_html(markdown_file, html_file):
    """使用MathJax将Markdown转换为HTML"""
    # 读取Markdown文件
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # 获取源文件的目录
    source_file_dir = os.path.dirname(os.path.abspath(markdown_file))
    if not source_file_dir:
        source_file_dir = os.getcwd()
        
    # 获取输出HTML的目录
    output_dir = os.path.dirname(os.path.abspath(html_file))
    if not output_dir:
        output_dir = os.getcwd()
    
    # 首先将Markdown转换为HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.nl2br'
        ]
    )
    
    # 然后预处理HTML中的公式标签
    processed_html = preprocess_math_tags_for_mathjax(html_content)
    
    # 修复图片路径并复制图片文件
    processed_html = fix_image_paths(processed_html, source_file_dir, output_dir)
    
    # HTML模板，包含启用MathJax的JavaScript，大幅增加公式字体大小
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LaTeX公式渲染测试</title>
    <script type="text/x-mathjax-config">
        MathJax.Hub.Config({{
            tex2jax: {{
                inlineMath: [['$','$']],
                displayMath: [['$$','$$']],
                processEscapes: true
            }},
            "HTML-CSS": {{ 
                scale: 100,              // 极大增加公式大小至原来的200%
                availableFonts: ["STIX"],
                preferredFont: "STIX",
                webFont: "STIX-Web",
                imageFont: null,
                matchFontHeight: true
            }},
            CommonHTML: {{
                scale: 200               // 同样增加CommonHTML输出的大小
            }},
            SVG: {{
                scale: 200,              // 增加SVG输出的大小
                blacker: 10,             // 使字体更黑更清晰
                font: "STIX-Web"
            }}
        }});
    </script>
    <script type="text/javascript" async
        src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 2cm;
            font-size: 12pt;
        }}
        h1 {{ font-size: 20pt; margin-top: 1.5em; margin-bottom: 0.8em; }}
        h2 {{ font-size: 16pt; margin-top: 1.3em; margin-bottom: 0.7em; }}
        h3 {{ font-size: 14pt; margin-top: 1.2em; margin-bottom: 0.6em; }}
        pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 5px; }}
        code {{ font-family: Consolas, monospace; }}
        
        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse; /* 合并边框 */
            margin: 1.5em 0;
            border: 1px solid #ddd; /* 外部边框 */
        }}
        th, td {{
            border: 1px solid #ddd; /* 内部边框 */
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        
        /* 使用直接缩放变换增大MathJax元素 */
        .MathJax_Display {{
            font-size: 100% !important;
            transform: scale(1.0) !important;
            transform-origin: left center !important;
            margin: 1em 0 2em 0 !important;
            width: 100% !important;
        }}
        
        .MathJax {{
            font-size: 100% !important; 
            transform: scale(1.5) !important;
            transform-origin: center !important;
            margin: 0 0.5em !important;
        }}
        
        /* 设置公式容器的大小和边距 */
        .MathJax_SVG_Display {{ 
            margin: 2em 0 !important;
            padding: 0.5em !important;
            background-color: #f9f9f9 !important;
            border-radius: 8px !important;
        }}
        
        .MathJax_SVG {{
            transform: scale(1.8) !important;
            transform-origin: center !important;
        }}
        
        /* 图片样式 */
        img {{
            max-width: 90%;
            height: auto;
            display: block;
            margin: 1.5em auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        /* 图片说明文字 */
        img + p {{
            text-align: center;
            font-style: italic;
            margin-top: -0.5em;
            color: #555;
        }}
    </style>
</head>
<body>
{0}
</body>
</html>"""
    
    # 生成完整HTML
    full_html = html_template.format(processed_html)
    
    # 保存HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    return html_file

# wkhtmltopdf参数:
# --dpi <dpi>         : 设置DPI分辨率(默认96，建议300-1200)
# --image-dpi <dpi>   : 设置图像DPI分辨率
# --image-quality <n> : 设置图像质量(0-100)
# --zoom <factor>     : 设置页面缩放因子(1.0-3.0)
# --javascript-delay <msec> : 等待JavaScript执行的时间(毫秒)

def html_to_pdf(html_file, pdf_file, wkhtmltopdf_path, pdf_options=None):
    """使用wkhtmltopdf将HTML转换为PDF"""
    try:
        # 确保路径被正确引用
        if " " in wkhtmltopdf_path and not wkhtmltopdf_path.startswith('"'):
            wkhtmltopdf_path = f'"{wkhtmltopdf_path}"'
            
        # 显式创建配置对象
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        
        # 定义wkhtmltopdf的默认选项
        options = {
            'encoding': "UTF-8",
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            '--enable-local-file-access': None,  # 允许访问本地文件
        }

        # 合并用户自定义选项
        if pdf_options:
            options.update(pdf_options)
        
        # 转换并处理可能的超时
        # 注意：pdfkit在Windows上可能会有bug，即使成功也可能抛出OSError。
        # 如果错误信息包含 "Done", "loaded" 等关键字，我们认为它是成功的。
        pdfkit.from_file(html_file, pdf_file, configuration=config, options=options)
        
        print(f"成功将HTML转换到PDF: {pdf_file}")
        
    except FileNotFoundError:
        print(f"错误: 'wkhtmltopdf'未找到。请确保它已安装并位于系统PATH中。")
        return False
    except Exception as e:
        print(f"将HTML转换为PDF时发生未知错误: {e}")
        return False

def process_markdown_to_pdf(input_file, output_file, wkpath=None, keep_html=False,
                            page_size='A4', orientation='Portrait', 
                            margin_top='15mm', margin_right='15mm', 
                            margin_bottom='15mm', margin_left='15mm'):
    """
    处理完整的Markdown到PDF转换流程。
    新增PDF样式参数。
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        return

    # 定义临时HTML文件路径
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(output_file)), 'temp_output')
    os.makedirs(temp_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    html_output_path = os.path.join(temp_dir, f"{base_name}.html")

    # Step 1: Convert Markdown to HTML with MathJax support
    markdown_to_html(input_file, html_output_path)
    
    # Step 2: Determine wkhtmltopdf path
    if wkpath and os.path.exists(wkpath):
        wkhtmltopdf_path = wkpath
    else:
        # 否则，尝试从通用位置或PATH中找到它
        try:
            # 对于Windows， अक्सर在Program Files中
            possible_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
            if os.path.exists(possible_path):
                 wkhtmltopdf_path = possible_path
            else:
                # 对于Linux/macOS，通常在PATH中
                wkhtmltopdf_path = subprocess.check_output(['which', 'wkhtmltopdf']).strip().decode('utf-8')
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("错误: 无法自动找到wkhtmltopdf。请使用 --wkpath 参数指定路径。")
            # 清理临时文件后退出
            if not keep_html and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return

    # Step 3: Convert HTML to PDF with new options
    pdf_output_path = output_file
    
    # 构建PDF选项字典
    pdf_options = {
        'page-size': page_size,
        'orientation': orientation,
        'margin-top': margin_top,
        'margin-right': margin_right,
        'margin-bottom': margin_bottom,
        'margin-left': margin_left,
    }

    html_to_pdf(html_output_path, pdf_output_path, wkhtmltopdf_path, pdf_options)

    # Step 4: Clean up temporary files
    if not keep_html:
        try:
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录: {temp_dir}")
        except OSError as e:
            print(f"清理临时目录时出错: {e}")

def main():
    """主函数，用于命令行执行"""
    parser = argparse.ArgumentParser(description="将Markdown文件（包括复杂的LaTeX公式）转换为高质量的PDF。")
    parser.add_argument("input_file", help="输入的Markdown文件路径。")
    parser.add_argument("-o", "--output", help="输出的PDF文件路径。如果未提供，则默认为输入文件名（扩展名更改为.pdf）。")
    parser.add_argument("--wkpath", help="wkhtmltopdf的可执行文件路径。如果未提供，脚本会尝试在环境变量中查找。")
    parser.add_argument("--keep-html", action="store_true", help="保留转换过程中生成的中间HTML文件。")
    # 新增PDF样式选项
    parser.add_argument('--page-size', default='A4', help='PDF页面大小 (例如: A4, Letter)。 默认: A4')
    parser.add_argument('--orientation', default='Portrait', choices=['Portrait', 'Landscape'], help='页面方向 (Portrait 或 Landscape)。 默认: Portrait')
    parser.add_argument('--margin-top', default='15mm', help='上边距 (例如: 10mm)。 默认: 15mm')
    parser.add_argument('--margin-right', default='15mm', help='右边距 (例如: 10mm)。 默认: 15mm')
    parser.add_argument('--margin-bottom', default='15mm', help='下边距 (例如: 10mm)。 默认: 15mm')
    parser.add_argument('--margin-left', default='15mm', help='左边距 (例如: 10mm)。 默认: 15mm')

    args = parser.parse_args()

    # 确定输出文件路径
    if args.output:
        output_file = args.output
    else:
        output_file = os.path.splitext(args.input_file)[0] + ".pdf"

    # 处理文件
    process_markdown_to_pdf(
        args.input_file, 
        output_file, 
        args.wkpath, 
        args.keep_html,
        page_size=args.page_size,
        orientation=args.orientation,
        margin_top=args.margin_top,
        margin_right=args.margin_right,
        margin_bottom=args.margin_bottom,
        margin_left=args.margin_left
    )


if __name__ == '__main__':
    main() 