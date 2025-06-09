import os
import sys
import argparse

# 将src目录添加到系统路径中，以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pdf_to_markdown import to_markdown
from translate_markdown import translate_file
from markdown_to_pdf import process_markdown_to_pdf

def run_full_process(pdf_file, output_dir="output", skip_translation=False, keep_intermediate=False):
    """
    执行完整的PDF到PDF处理流程。
    这是一个生成器函数，会逐步yield日志信息。
    
    :param pdf_file: 输入的PDF文件路径
    :param output_dir: 输出目录
    :param skip_translation: 是否跳过翻译步骤
    :param keep_intermediate: 是否保留中间文件
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
        translated_md_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(md_path))[0]}_translated.md")
        translate_file(md_path, translated_md_path)
        yield f"翻译后的Markdown文件: {translated_md_path}"
        final_md_path = translated_md_path
    else:
        yield "\n--- 步骤 2: 已跳过翻译 ---"

    # --- 步骤 3: Markdown to PDF ---
    yield "\n--- 步骤 3: 将Markdown转换为PDF ---"
    pdf_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(final_md_path))[0]}.pdf")
    
    # 直接调用处理函数
    process_markdown_to_pdf(
        input_file=final_md_path,
        output_file=pdf_output_path,
        keep_html=keep_intermediate
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
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"错误: 输入的PDF文件不存在: {args.pdf_file}")
        return
        
    # 由于run_full_process现在是生成器，我们需要迭代它来执行并打印日志
    # 在命令行模式下，我们对最终的返回路径不感兴趣，只打印日志
    for log_message in run_full_process(args.pdf_file, args.output, args.skip_translation, args.keep_intermediate):
        print(log_message)

if __name__ == "__main__":
    main() 