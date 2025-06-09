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
        
        /* 表格样式 */
        table {{
            border-collapse: collapse; /* 合并边框 */
            width: 100%;
            margin: 1.5em 0;
        }}
        table, th, td {{
            border: 1px solid black; /* 设置边框 */
        }}
        th, td {{
            padding: 8px; /* 内边距 */
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2; /* 表头背景色 */
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

def html_to_pdf(html_file, pdf_file, wkhtmltopdf_path):
    """将HTML转换为PDF，确保启用JavaScript以渲染MathJax"""
    # 检查wkhtmltopdf路径
    if not os.path.exists(wkhtmltopdf_path):
        print(f"错误: wkhtmltopdf可执行文件不存在: {wkhtmltopdf_path}")
        return False
    
    # 设置命令，必须启用JavaScript支持，并增加DPI使字体更清晰
    cmd = [
        wkhtmltopdf_path,
        '--encoding', 'UTF-8',
        '--enable-javascript',           # 启用JavaScript渲染
        '--javascript-delay', '10000',   # 增加等待时间到10秒确保MathJax完全渲染
        '--dpi', '600',                  # 显著增加DPI提高清晰度
        '--image-dpi', '600',            # 增加图像DPI
        '--image-quality', '100',        # 最高图像质量
        '--zoom', '1.5',                 # 整体页面缩放150%
        '--page-size', 'A4',
        '--margin-top', '1cm',
        '--margin-right', '1cm',
        '--margin-bottom', '1cm',
        '--margin-left', '1cm',
        '--no-outline',
        '--enable-local-file-access',    # 允许访问本地文件(重要！用于加载本地图片)
        '--enable-external-links',       # 启用外部链接
        '--images',                      # 加载图片
        '--print-media-type',            # 使用打印媒体类型的CSS规则
        '--no-stop-slow-scripts',        # 不停止慢脚本
        html_file,
        pdf_file
    ]
    
    # 执行命令
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 输出日志
    if result.stdout:
        print(f"命令输出: {result.stdout}")
    if result.stderr:
        print(f"警告/错误: {result.stderr}")
    
    # 检查是否成功
    if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
        print(f"PDF生成成功，已保存到 {pdf_file}")
        return True
    else:
        print(f"PDF生成失败，返回码: {result.returncode}")
        return False

def main():
    """使用MathJax渲染LaTeX公式的测试脚本"""
    parser = argparse.ArgumentParser(description="使用MathJax渲染LaTeX公式的Markdown到PDF转换")
    parser.add_argument("-i", "--input", help="输入Markdown文件路径", default="测试pdf_translated.md")
    parser.add_argument("-o", "--output", help="输出PDF文件路径")
    parser.add_argument("--fonts", help="wkhtmltopdf可执行文件路径", 
                       default=r"C:\Users\55473\Desktop\配电房\wkhtmltopdf\bin\wkhtmltopdf.exe")
    args = parser.parse_args()
    
    # 获取输入文件路径
    input_file = args.input
    
    # 如果未指定输出文件，则自动生成
    if not args.output:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_mathjax.pdf"
    else:
        output_file = args.output
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return
    
    print(f"开始将 {input_file} 转换为带有MathJax渲染的PDF文件 {output_file} ...")
    
    # 生成临时HTML文件
    html_file = output_file + '.temp.html'
    markdown_to_html(input_file, html_file)
    print(f"临时HTML文件已生成: {html_file}")
    
    # 转换为PDF
    success = html_to_pdf(html_file, output_file, args.fonts)
    if success:
        print(f"转换完成！带MathJax渲染的PDF已保存到: {output_file}")
    else:
        print("转换失败，请检查错误信息。")

if __name__ == "__main__":
    main() 