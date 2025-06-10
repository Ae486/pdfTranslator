import os
import sys
import argparse

# 将src目录添加到系统路径中，以便导入模块
# 必须在导入自定义模块之前执行
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import config
from pdf_to_markdown import to_markdown
from translate_markdown import process_translation
from markdown_to_pdf import process_markdown_to_pdf

def update_config_file(app_id, app_key):
    """动态更新config.py文件中的百度API密钥"""
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'config.py')
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(config_path, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.strip().startswith('BAIDU_TRANSLATE_APP_ID'):
                f.write(f'BAIDU_TRANSLATE_APP_ID = "{app_id}"  # 请填入您的百度翻译APP ID\n')
            elif line.strip().startswith('BAIDU_TRANSLATE_APP_KEY'):
                f.write(f'BAIDU_TRANSLATE_APP_KEY = "{app_key}"  # 请填入您的百度翻译密钥\n')
            else:
                f.write(line)

def run_full_process(pdf_file, output_dir="output", skip_translation=False, keep_intermediate=False, 
                     from_lang='auto', to_lang='zh', baidu_app_id=None, baidu_app_key=None,
                     page_size='A4', orientation='Portrait', margin_top='15mm', 
                     margin_right='15mm', margin_bottom='15mm', margin_left='15mm'):
    """
    执行完整的PDF到PDF处理流程。
    这是一个生成器函数，会逐步yield日志信息。
    
    :param pdf_file: 输入的PDF文件路径
    :param output_dir: 输出目录
    :param skip_translation: 是否跳过翻译步骤
    :param keep_intermediate: 是否保留中间文件
    :param from_lang: 源语言
    :param to_lang: 目标语言
    :param baidu_app_id: 百度翻译APP ID (可选, 用于Web UI)
    :param baidu_app_key: 百度翻译密钥 (可选, 用于Web UI)
    :param page_size: PDF页面大小
    :param orientation: PDF页面方向
    :param margin_top: PDF上边距
    :param margin_right: PDF右边距
    :param margin_bottom: PDF下边距
    :param margin_left: PDF左边距
    :yield: (str) 日志信息
    :return: (str) 最终生成的PDF路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # --- 步骤 1: PDF to Markdown ---
    yield "\n--- 步骤 1: 将PDF转换为Markdown ---"
    md_result = to_markdown(pdf_file, output_dir)
    if md_result["status"] != "success":
        yield f"PDF到Markdown转换失败: {md_result.get('message', '未知错误')}"
        return
    
    md_path = md_result["markdown"]
    yield f"Markdown文件已生成: {md_path}"
    
    # --- 步骤 2: 翻译Markdown (可选) ---
    final_md_path = md_path
    if not skip_translation:
        yield "\n--- 步骤 2: 翻译Markdown文件 ---"
        
        # 确定使用哪个App ID和Key
        app_id = baidu_app_id or config.BAIDU_TRANSLATE_APP_ID
        app_key = baidu_app_key or config.BAIDU_TRANSLATE_APP_KEY

        # 如果是从Web UI调用的，我们不希望弹出命令行输入
        # 只有在命令行模式下 (baidu_app_id 为 None) 且配置为空时才提示
        if baidu_app_id is None and (not app_id or not app_key):
            yield "百度翻译API密钥未配置，请在下方输入："
            try:
                app_id = input("请输入百度翻译 APP ID: ")
                app_key = input("请输入百度翻译 APP KEY: ")
                if not app_id or not app_key:
                    yield "错误：APP ID 和 APP KEY 不能为空。"
                    return
                # 更新配置文件以便下次使用
                update_config_file(app_id, app_key)
                yield "API密钥已保存到 src/config.py"
            except Exception as e:
                yield f"读取输入或更新配置时出错: {e}"
                return

        translated_md_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(md_path))[0]}_translated.md")
        
        # 调用更新后的翻译函数
        translated_md_path, error = process_translation(
            md_path, 
            translated_md_path, 
            from_lang=from_lang, 
            to_lang=to_lang, 
            app_id=app_id, 
            app_key=app_key
        )
        
        if error:
            yield f"翻译失败: {error}"
            return
            
        yield f"翻译后的Markdown文件 ({from_lang} -> {to_lang}): {translated_md_path}"
        final_md_path = translated_md_path
    else:
        yield "\n--- 步骤 2: 已跳过翻译 ---"

    # --- 步骤 3: Markdown to PDF ---
    yield "\n--- 步骤 3: 将Markdown转换为PDF ---"
    pdf_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(final_md_path))[0]}.pdf")
    
    # 直接调用处理函数，并传递所有PDF选项
    process_markdown_to_pdf(
        input_file=final_md_path,
        output_file=pdf_output_path,
        keep_html=keep_intermediate,
        page_size=page_size,
        orientation=orientation,
        margin_top=margin_top,
        margin_right=margin_right,
        margin_bottom=margin_bottom,
        margin_left=margin_left
    )
    
    yield f"\n处理流程完成! 最终PDF文件保存在: {pdf_output_path}"

    # --- 步骤 4: 清理中间文件 ---
    if not keep_intermediate:
        yield "\n--- 步骤 4: 清理中间文件 ---"
        # 使用集合来处理，避免重复删除
        files_to_delete = {md_path, final_md_path}
        
        for file_path in files_to_delete:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    yield f"已删除中间文件: {file_path}"
            except Exception as e:
                yield f"清理中间文件 {file_path} 时出错: {e}"
    
    # 在最后，返回最终文件路径
    return pdf_output_path


def main():
    parser = argparse.ArgumentParser(description="一键完成PDF到PDF的转换、翻译和渲染流程")
    parser.add_argument("pdf_file", help="要处理的PDF文件路径")
    parser.add_argument("-o", "--output", default="output", help="输出目录")
    parser.add_argument("--skip-translation", action="store_true", help="如果设置，将跳过翻译步骤")
    parser.add_argument("--keep-intermediate", action="store_true", help="如果设置，将保留所有中间文件(如.md, .html)")
    parser.add_argument("--from-lang", default=config.SOURCE_LANG, help=f"源语言 (默认为: {config.SOURCE_LANG})")
    parser.add_argument("--to-lang", default=config.TARGET_LANG, help=f"目标语言 (默认为: {config.TARGET_LANG})")
    
    # 新增PDF样式相关的命令行参数
    parser.add_argument('--page-size', default='A4', help='PDF页面大小 (例如: A4, Letter)。 默认: A4')
    parser.add_argument('--orientation', default='Portrait', choices=['Portrait', 'Landscape'], help='页面方向 (Portrait 或 Landscape)。 默认: Portrait')
    parser.add_argument('--margin-top', default='15mm', help='上边距 (例如: 10mm)。 默认: 15mm')
    parser.add_argument('--margin-right', default='15mm', help='右边距 (例如: 10mm)。 默认: 15mm')
    parser.add_argument('--margin-bottom', default='15mm', help='下边距 (例如: 10mm)。 默认: 15mm')
    parser.add_argument('--margin-left', default='15mm', help='左边距 (例如: 10mm)。 默认: 15mm')

    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"错误: 输入的PDF文件不存在: {args.pdf_file}")
        return
        
    # 由于run_full_process现在是生成器，我们需要迭代它来执行并打印日志
    # 在命令行模式下，我们对最终的返回路径不感兴趣，只打印日志
    for log_message in run_full_process(
        args.pdf_file, 
        args.output, 
        args.skip_translation, 
        args.keep_intermediate,
        from_lang=args.from_lang,
        to_lang=args.to_lang,
        page_size=args.page_size,
        orientation=args.orientation,
        margin_top=args.margin_top,
        margin_right=args.margin_right,
        margin_bottom=args.margin_bottom,
        margin_left=args.margin_left
    ):
        print(log_message)

if __name__ == "__main__":
    main() 