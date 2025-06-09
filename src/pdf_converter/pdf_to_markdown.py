import os
import json
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

def pdf_to_markdown(pdf_file_path, output_base_dir="output"):
    """
    将PDF文件转换为Markdown格式，同时提取图片
    
    参数:
        pdf_file_path: 输入的PDF文件路径
        output_base_dir: 输出文件的基础目录
    
    返回:
        dict: 包含处理结果的字典，包括:
            - status: 'success'或'error'
            - markdown: 生成的Markdown文件路径
            - output_dir: 输出目录的绝对路径
            - message: 如果出错，包含错误信息
    """
    # 准备输出目录结构
    name_without_suff = os.path.splitext(os.path.basename(pdf_file_path))[0]
    local_image_dir = os.path.join(output_base_dir, "images")
    local_md_dir = output_base_dir
    image_dir = os.path.basename(local_image_dir)  # 仅获取目录名，不包含路径
    
    # 创建输出目录
    os.makedirs(local_image_dir, exist_ok=True)
    os.makedirs(local_md_dir, exist_ok=True)
    
    # 初始化写入器
    image_writer = FileBasedDataWriter(local_image_dir)
    md_writer = FileBasedDataWriter(local_md_dir)
    
    # 读取PDF文件
    print(f"正在读取PDF文件: {pdf_file_path}")
    reader = FileBasedDataReader("")
    pdf_bytes = reader.read(pdf_file_path)
    
    try:
        # 创建数据集实例
        print("正在初始化PDF分析器...")
        ds = PymuDocDataset(pdf_bytes)
        
        # 分类并处理PDF
        print("正在分析PDF类型...")
        if ds.classify() == SupportedPdfParseMethod.OCR:
            print("检测为OCR类型PDF，使用OCR模式处理...")
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            print("检测为文本类型PDF，使用文本模式处理...")
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)
        
        # 生成并保存Markdown
        print("生成Markdown文档...")
        md_content = pipe_result.get_markdown(image_dir)
        md_path = os.path.join(local_md_dir, f"{name_without_suff}.md")
        pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
        
        print("\n处理完成! Markdown文件已保存:")
        print(f"Markdown文档: {md_path}")
        print(f"图片目录: {os.path.abspath(local_image_dir)}")
        
        return {
            "status": "success",
            "markdown": md_path,
            "output_dir": os.path.abspath(output_base_dir)
        }
        
    except Exception as e:
        error_msg = f"处理PDF时出错: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

def main():
    """命令行入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="将PDF文件转换为Markdown格式")
    parser.add_argument("pdf_path", help="PDF文件的路径")
    parser.add_argument("-o", "--output", default="output", help="输出目录路径，默认为'output'")
    
    args = parser.parse_args()
    
    result = pdf_to_markdown(args.pdf_path, args.output)
    
    if result["status"] == "success":
        print(f"\n转换成功! Markdown文件保存在: {result['markdown']}")
    else:
        print(f"\n转换失败: {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main() 