import os
import json
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

def process_pdf(pdf_file_path, output_base_dir="output"):
    """
    处理PDF文件并生成所有输出文件
    
    参数:
        pdf_file_path: 输入的PDF文件路径
        output_base_dir: 输出文件的基础目录
    
    生成的文件:
        - {pdf_name}_model.pdf: 模型推理结果可视化
        - {pdf_name}_model.json: 模型原始推理结果
        - {pdf_name}_layout.pdf: 布局分析结果可视化
        - {pdf_name}_spans.pdf: 文本span分析结果可视化
        - {pdf_name}.md: 转换后的Markdown文档
        - {pdf_name}_content_list.json: 内容列表JSON
        - {pdf_name}_middle.json: 中间处理结果JSON
        - images/: 存放提取的图片
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
        
        # 生成模型结果可视化PDF
        print("生成模型结果可视化PDF...")
        model_pdf_path = os.path.join(local_md_dir, f"{name_without_suff}_model.pdf")
        infer_result.draw_model(model_pdf_path)
        
        # 获取并保存模型原始推理结果
        print("保存模型原始推理结果JSON...")
        model_inference_result = infer_result.get_infer_res()
        model_json_path = os.path.join(local_md_dir, f"{name_without_suff}_model.json")
        with open(model_json_path, 'w', encoding='utf-8') as f:
            json.dump(model_inference_result, f, ensure_ascii=False, indent=2)
        
        # 生成布局可视化PDF
        print("生成布局分析结果PDF...")
        layout_pdf_path = os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf")
        pipe_result.draw_layout(layout_pdf_path)
        
        # 生成spans可视化PDF
        print("生成文本span分析结果PDF...")
        spans_pdf_path = os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf")
        pipe_result.draw_span(spans_pdf_path)
        
        # 生成并保存Markdown
        print("生成Markdown文档...")
        md_content = pipe_result.get_markdown(image_dir)
        md_path = os.path.join(local_md_dir, f"{name_without_suff}.md")
        pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
        
        # 生成并保存内容列表JSON
        print("生成内容列表JSON...")
        content_list_path = os.path.join(local_md_dir, f"{name_without_suff}_content_list.json")
        pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)
        
        # 生成并保存中间JSON
        print("生成中间处理结果JSON...")
        middle_json_path = os.path.join(local_md_dir, f"{name_without_suff}_middle.json")
        pipe_result.dump_middle_json(md_writer, f"{name_without_suff}_middle.json")
        
        print("\n处理完成! 所有输出文件已保存到以下路径:")
        print(f"输出目录: {os.path.abspath(output_base_dir)}")
        print(f"模型结果可视化: {model_pdf_path}")
        print(f"模型原始数据: {model_json_path}")
        print(f"布局分析结果: {layout_pdf_path}")
        print(f"文本span分析: {spans_pdf_path}")
        print(f"Markdown文档: {md_path}")
        print(f"内容列表: {content_list_path}")
        print(f"中间处理结果: {middle_json_path}")
        
        return {
            "status": "success",
            "output_dir": os.path.abspath(output_base_dir),
            "model_pdf": model_pdf_path,
            "model_json": model_json_path,
            "layout_pdf": layout_pdf_path,
            "spans_pdf": spans_pdf_path,
            "markdown": md_path,
            "content_list": content_list_path,
            "middle_json": middle_json_path
        }
        
    except Exception as e:
        error_msg = f"处理PDF时出错: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# 使用示例
if __name__ == "__main__":
    # 替换为你的PDF文件路径
    input_pdf = "C:\\Users\\55473\\Desktop\\测试pdf.pdf"
    
    # 替换为你想要的输出目录（可选）
    output_dir = "output"
    
    # 处理PDF
    result = process_pdf(input_pdf, output_dir)
    
    # 打印处理结果
    print("\n处理状态:", result.get("status"))
    if result.get("status") == "error":
        print("错误信息:", result.get("message"))